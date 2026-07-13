meta:
  id: e_lenprefix_017
  endian: be
seq:
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
