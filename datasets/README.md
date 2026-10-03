# FloorMess dataset status

No real dataset or trained weights are included. Use the collection, explicit annotation,
validation and grouped-export commands in [PERCEPTION.md](../docs/PERCEPTION.md).
Never treat missing annotation files as negative examples. Preserve collection-session,
room and household groups to keep correlated footage together. Configurable visual
signatures detect near-duplicates and link matching sessions before splitting. Review
the generated comparison reports: the heuristic cannot guarantee detection of every
similar frame or preservation of every subtle cable. Cable-positive annotations are
retained for approximate matches, and missing annotations have no such protection.
