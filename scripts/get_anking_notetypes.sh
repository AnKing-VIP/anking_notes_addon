#!/bin/bash
# Download notetype templates from AnKingMed/AnKing-Note-Types repository

gitdir https://github.com/RisingOrange/AnKing-Note-Types/tree/master/Note%20Types

# gitdir gets confused by %20 (urlencoded whitespace)
rm -r Note%20Types

rm -r src/anking_notetypes/note_types
mv "Note Types" src/anking_notetypes/note_types