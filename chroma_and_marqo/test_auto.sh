#!/bin/bash

# Variables to configure
SOURCE_PDF="./pdf_folder/short-stories2.pdf"
#DEST_PDF="./pdf_folder/copied.pdf"
BUILD_SCRIPT="build_thing_chroma.py"
TEST_SCRIPT="test_chroma.py"
BUILD_RUNS=3
TEST_RUNS=2
REPEAT=6

for ((i=1; i<=REPEAT; i++))
do
    echo "=== Iteration $i ==="
  
  # Copy the PDF
  # Count how many PDFs are currently in the folder
    num_pdfs=$(ls ./pdf_folder/*.pdf 2>/dev/null | wc -l)

    # Set destination PDF name using that count (e.g. copied_5.pdf)
    DEST_PDF="./pdf_folder/copied_${num_pdfs}.pdf"

    cp "$SOURCE_PDF" "$DEST_PDF"
    echo "Copied $SOURCE_PDF to $DEST_PDF"
    
    # Run build script multiple times
    for ((j=1; j<=BUILD_RUNS; j++))
        do
            echo "Running $BUILD_SCRIPT - Run $j"
            python3 "$BUILD_SCRIPT"
        done
    
    # Run test script multiple times
    for ((k=1; k<=TEST_RUNS; k++))
        do
            echo "Running $TEST_SCRIPT - Run $k"
            python3 "$TEST_SCRIPT"
        done
  
done
