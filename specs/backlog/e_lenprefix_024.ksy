meta:
  id: e_lenprefix_024
  endian: be
seq:
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
