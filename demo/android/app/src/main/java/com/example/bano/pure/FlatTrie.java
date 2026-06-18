package com.example.bano.pure;

import java.util.HashMap;
import java.util.Map;

/**
 * Trie aplati en tableaux d'int, numérotation PRÉORDRE : le sous-arbre d'un
 * nœud occupe la plage contiguë [id, subtreeEnd[id]) — la collecte d'un
 * préfixe devient un simple balayage de tableau (cache-friendly), sans
 * pointeurs ni boxing. Les enfants d'un nœud sont triés par code point
 * (recherche binaire dans {@link #child}).
 */
public final class FlatTrie {
    /** Index vocab de la feuille, ou -1 si le nœud n'est pas une fin de jeton. */
    public final int[] leaf;
    /** Fin (exclusive) de la plage préordre du sous-arbre du nœud. */
    public final int[] subtreeEnd;
    /** Début des enfants du nœud dans childCp/childNode. */
    public final int[] childStart;
    public final int[] childCount;
    /** Code points des arêtes, triés par nœud. */
    public final int[] childCp;
    public final int[] childNode;

    public static final int ROOT = 0;

    private FlatTrie(int[] leaf, int[] subtreeEnd, int[] childStart, int[] childCount,
                     int[] childCp, int[] childNode) {
        this.leaf = leaf;
        this.subtreeEnd = subtreeEnd;
        this.childStart = childStart;
        this.childCount = childCount;
        this.childCp = childCp;
        this.childNode = childNode;
    }

    /** Enfant de {@code node} portant {@code cp}, ou -1. Recherche binaire. */
    public int child(int node, int cp) {
        int lo = childStart[node];
        int hi = lo + childCount[node] - 1;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            int v = childCp[mid];
            if (v < cp) lo = mid + 1;
            else if (v > cp) hi = mid - 1;
            else return childNode[mid];
        }
        return -1;
    }

    /** Construction : trie à pointeurs temporaire, puis aplatissement préordre. */
    public static final class Builder {
        private static final class Node {
            final Map<Integer, Node> children = new HashMap<>();
            int leaf = -1;
        }

        private final Node root = new Node();
        private int nodes = 1;
        private int edges = 0;

        public void insert(String token, int vocabIndex) {
            Node cur = root;
            for (int i = 0; i < token.length(); ) {
                int cp = token.codePointAt(i);
                i += Character.charCount(cp);
                Node next = cur.children.get(cp);
                if (next == null) {
                    next = new Node();
                    cur.children.put(cp, next);
                    nodes++;
                    edges++;
                }
                cur = next;
            }
            cur.leaf = vocabIndex;
        }

        public FlatTrie build() {
            int[] leaf = new int[nodes];
            int[] subtreeEnd = new int[nodes];
            int[] childStart = new int[nodes];
            int[] childCount = new int[nodes];
            int[] childCp = new int[edges];
            int[] childNode = new int[edges];

            // Parcours préordre itératif. Chaque frame garde le curseur sur ses
            // enfants triés ; subtreeEnd est posé quand le frame est épuisé.
            final class Frame {
                final int id;
                final int edgeBase;
                final Node[] kids;
                int k = 0;

                Frame(Node n, int id, int nextEdge) {
                    this.id = id;
                    this.edgeBase = nextEdge;
                    int len = n.children.size();
                    int[] cps = new int[len];
                    kids = new Node[len];
                    int i = 0;
                    for (Map.Entry<Integer, Node> e : n.children.entrySet()) {
                        cps[i] = e.getKey();
                        kids[i] = e.getValue();
                        i++;
                    }
                    // Tri par insertion (peu d'enfants par nœud : lettres/chiffres).
                    for (int a = 1; a < len; a++) {
                        int cp = cps[a];
                        Node kd = kids[a];
                        int b = a - 1;
                        while (b >= 0 && cps[b] > cp) {
                            cps[b + 1] = cps[b];
                            kids[b + 1] = kids[b];
                            b--;
                        }
                        cps[b + 1] = cp;
                        kids[b + 1] = kd;
                    }
                    leaf[id] = n.leaf;
                    childStart[id] = edgeBase;
                    childCount[id] = len;
                    System.arraycopy(cps, 0, childCp, edgeBase, len);
                }
            }

            java.util.ArrayDeque<Frame> stack = new java.util.ArrayDeque<>();
            int nextId = 0;
            int nextEdge = 0;
            Frame rf = new Frame(root, nextId++, nextEdge);
            nextEdge += rf.kids.length;
            stack.push(rf);
            while (!stack.isEmpty()) {
                Frame f = stack.peek();
                if (f.k < f.kids.length) {
                    Node child = f.kids[f.k];
                    int childId = nextId++;
                    childNode[f.edgeBase + f.k] = childId;
                    f.k++;
                    Frame cf = new Frame(child, childId, nextEdge);
                    nextEdge += cf.kids.length;
                    stack.push(cf);
                } else {
                    subtreeEnd[f.id] = nextId;
                    stack.pop();
                }
            }

            return new FlatTrie(leaf, subtreeEnd, childStart, childCount, childCp, childNode);
        }
    }
}
