# Pre-send composer capture

The original pre-send observation was a character-presence/order check on the rendered rich editor, performed immediately before the single Send action. Every expected prompt character was present and in order. The rendered editor normalized whitespace by inserting 217 blank-line characters and two trailing newline characters; this was recorded as a rendering-only difference.

The complete pre-send composer string was not retained as an independent archival string after the send. It is therefore not recreated here and no historical composer text is claimed. The available evidence is the actual check above, plus the exact source prompt record: 23,431 UTF-8 bytes, SHA-256 `e91f1beb4fe40f38eabe67488d9a98163e195437be6f9eb6d9937f030a41a59f`.

This limitation does not affect the accepted-node capture: [ACCEPTED_USER_NODE.txt](ACCEPTED_USER_NODE.txt) contains the complete read-only same-node body capture, whose captured body is 23,294 bytes and SHA-256 `44dd2c9414a2f94287ded8aa47ad47a700436bbb6877daecf8f658690c1c1b44`. The text-file container has one archival terminal LF; see [ACCEPTED_USER_NODE_RECEIPT.json](ACCEPTED_USER_NODE_RECEIPT.json).
