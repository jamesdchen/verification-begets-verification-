meta:
  id: e_lenprefix_000
  endian: le
seq:
  - id: f0
    type: u2
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
