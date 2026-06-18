package com.example.bano.pure;

import org.apache.lucene.store.ByteArrayDataInput;
import org.apache.lucene.util.BytesRef;
import org.apache.lucene.util.IntsRefBuilder;
import org.apache.lucene.util.automaton.Automata;
import org.apache.lucene.util.automaton.Automaton;
import org.apache.lucene.util.automaton.ByteRunAutomaton;
import org.apache.lucene.util.automaton.CompiledAutomaton;
import org.apache.lucene.util.automaton.LevenshteinAutomata;
import org.apache.lucene.util.automaton.Operations;
import org.apache.lucene.util.fst.Builder;
import org.apache.lucene.util.fst.FST;
import org.apache.lucene.util.fst.PositiveIntOutputs;
import org.apache.lucene.util.fst.Util;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

/**
 * {@link TokenMatcher} sur FST Lucene (module {@code lucene-core}, 8.x compatible ART).
 *
 * <p>Le FST mappe jeton -> index vocab (sortie {@code Long}). Les jetons sont déjà
 * triés en ordre croissant d'octets côté build (contrainte du {@link Builder}), et
 * l'index vocab i = position triée -> sortie = i.</p>
 *
 * <p><b>Algo = intersection FST ∩ automate</b> (comme le Rust : {@code Levenshtein.union(prefix)}
 * + {@code map.search(aut)}). On compile un automate déterministe d'octets = union(automate de
 * Levenshtein &le; maxDist, « commence par qtok »), puis on fait un DFS produit FST × automate :
 * chaque arc dont l'octet n'a pas de transition (step == -1) élague tout son sous-arbre. C'est ce
 * qui exploite le partage de suffixes du FST pour le flou — pas un simple parcours en trie.</p>
 *
 * <p>Parité : même ensemble retenu que {@link FlatTrieMatcher} (Levenshtein classique sans
 * transposition + préfixe), puis {@link PureIndex} applique le scoring. Jetons normalisés = ASCII,
 * donc « octet » == « code point » (unité du FST Rust de référence).</p>
 */
public final class FstMatcher implements TokenMatcher {
    private final FST<Long> fst;
    private final PositiveIntOutputs outputs = PositiveIntOutputs.getSingleton();

    /** Construit le FST en RAM depuis les jetons (fallback si pas de prébuild). */
    public FstMatcher(String[] tokens) {
        try {
            Builder<Long> builder = new Builder<>(FST.INPUT_TYPE.BYTE1, outputs);
            IntsRefBuilder scratch = new IntsRefBuilder();
            // Sortie = index vocab + 1 : PositiveIntOutputs réserve 0 (NO_OUTPUT),
            // donc on décale pour que l'index 0 reste représentable. -1 au marquage.
            for (int i = 0; i < tokens.length; i++) {
                builder.add(Util.toIntsRef(new BytesRef(tokens[i]), scratch), (long) (i + 1));
            }
            this.fst = builder.finish();
        } catch (IOException e) {
            throw new RuntimeException("construction FST Lucene", e);
        }
    }

    /** Charge un FST prébuild ({@code lucene.fst}, format Lucene) — pas de reconstruction. */
    public FstMatcher(File fstFile) {
        try {
            byte[] bytes = Files.readAllBytes(fstFile.toPath());
            // save(Path) a écrit meta + corps en séquence -> un seul DataInput pour les deux.
            ByteArrayDataInput in = new ByteArrayDataInput(bytes);
            this.fst = new FST<>(in, in, outputs);
        } catch (IOException e) {
            throw new RuntimeException("chargement FST Lucene " + fstFile, e);
        }
    }

    @Override
    public void match(String qtok, int maxDist, long[] matched, long deadlineNanos) {
        try {
            ByteRunAutomaton run = buildAutomaton(qtok, maxDist);
            FST.BytesReader reader = fst.getBytesReader();
            FST.Arc<Long> root = fst.getFirstArc(new FST.Arc<>());
            // État initial d'un RunAutomaton Lucene = 0.
            intersect(root, 0, 0L, run, matched, deadlineNanos, reader, new int[]{0});
        } catch (IOException e) {
            throw new RuntimeException("parcours FST Lucene", e);
        }
    }

    /** Automate d'octets déterministe = union(Levenshtein &le; maxDist, « commence par qtok »). */
    private static ByteRunAutomaton buildAutomaton(String qtok, int maxDist) {
        // Levenshtein classique (sans transposition) pour coller au FlatTrie et au Rust.
        Automaton lev = new LevenshteinAutomata(qtok, false).toAutomaton(maxDist);
        Automaton prefix = Operations.concatenate(Automata.makeString(qtok), Automata.makeAnyString());
        Automaton union = Operations.union(lev, prefix);
        // isBinary=FALSE : l'automate est sur des CODE POINTS (UTF-32). CompiledAutomaton
        // applique alors UTF32ToUTF8 -> automate d'octets UTF-8 qui PRÉSERVE le langage :
        // une suite d'octets est acceptée ssi la chaîne décodée est à distance <= maxDist.
        // C'est la distance PAR CARACTÈRE (comme `fst::Levenshtein` Rust et FlatTrie sur
        // code points). isBinary=true garderait l'automate code-point et le ferait avancer
        // octet par octet -> les jetons non-ASCII (œ, °, ᵉ... = UTF-8 multi-octets) seraient
        // comptés en octets, divergeant du Rust. simplify=false -> type NORMAL (runAutomaton non-null).
        CompiledAutomaton ca = new CompiledAutomaton(
                union, null, false, Operations.DEFAULT_DETERMINIZE_WORK_LIMIT, false);
        return ca.runAutomaton;
    }

    /**
     * DFS produit FST × automate. À chaque arc, {@code run.step} fait avancer l'automate ;
     * {@code step == -1} (octet refusé) élague tout le sous-arbre. Un arc final dont l'état
     * automate est acceptant => jeton retenu.
     */
    private void intersect(FST.Arc<Long> node, int autState, long acc, ByteRunAutomaton run,
                           long[] matched, long deadline, FST.BytesReader reader, int[] guard)
            throws IOException {
        if (!FST.targetHasArcs(node)) return;
        FST.Arc<Long> arc = fst.readFirstRealTargetArc(node.target(), new FST.Arc<>(), reader);
        while (true) {
            if ((++guard[0] & 511) == 0 && System.nanoTime() > deadline) {
                throw new PureIndex.TimeoutException("search deadline (FST ∩ automate)");
            }
            int ns = run.step(autState, arc.label() & 0xFF);
            if (ns != -1) {                       // octet accepté par l'automate
                long out = acc + arc.output();    // PositiveIntOutputs.add = addition (NO_OUTPUT=0)
                if (arc.isFinal() && run.isAccept(ns)) {
                    mark(matched, out + arc.nextFinalOutput());
                }
                intersect(arc, ns, out, run, matched, deadline, reader, guard);
            }
            if (arc.isLast()) break;
            arc = fst.readNextRealArc(arc, reader);
        }
    }

    /** {@code output} = index vocab + 1 (décalage anti-NO_OUTPUT). */
    private static void mark(long[] matched, long output) {
        int vi = (int) output - 1;
        matched[vi >>> 6] |= 1L << vi;
    }
}
