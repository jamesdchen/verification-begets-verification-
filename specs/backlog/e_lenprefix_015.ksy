meta:
  id: e_lenprefix_015
  endian: le
seq:
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
