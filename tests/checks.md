# Test cases

- Table exists
- PK exists in the table
- No overlapping columns exept for PK
- Check for different data types of the same column
 

# Functionality

- Get columns with types (may raise table not exist error) (📦 Adapter)
- Get columns only in A (🚒 engine)
- Get columns only in B (🚒 engine)
- Get overlapping columns (🚒 engine)
- Get Rows number (📦 Adapter)
- Get number of duplicate PKs (📦 Adapter)
- Get counts of different PKs (📦 Adapter)
    - get PK only in A
    - get PK only in B
    - get PK that are the same
    - get PK that are different
