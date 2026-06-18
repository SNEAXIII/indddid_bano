# search_bench/engines/__init__.py
from search_bench.engines.arrow_scan import ArrowScan
from search_bench.engines.csv_scan import CsvLinearScan
from search_bench.engines.fts5_trigram import Fts5Trigram
from search_bench.engines.fts5_unicode61 import Fts5Unicode61
from search_bench.engines.inverted_index import InvertedIndex
from search_bench.engines.like_baseline import LikeBaseline
from search_bench.engines.parquet_scan import ParquetScan
from search_bench.engines.trie_prefix import TriePrefix
from search_bench.engines.trigram_levenshtein import TrigramLevenshtein

ENGINES = [
    CsvLinearScan,
    TriePrefix,
    InvertedIndex,
    TrigramLevenshtein,
    LikeBaseline,
    Fts5Unicode61,
    Fts5Trigram,
    ParquetScan,
    ArrowScan,
]
