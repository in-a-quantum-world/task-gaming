# Token and message-structure report

These are actual counts of the locally rendered prompts under the pinned public Kimi K2 Thinking tokenizer and chat template. They are **an approximation to the provider input**, not measured OpenRouter/Novita billing counts. Provider-billed input tokens are unknown. All conditions use the same accounting rule.

The official [Kimi K2 Thinking tokenizer assets](https://huggingface.co/moonshotai/Kimi-K2-Thinking/tree/a51ccc050d73dab088bf7b0e2dd9b30ae85a4e55) are pinned to revision `a51ccc050d73dab088bf7b0e2dd9b30ae85a4e55` and included with their Modified MIT license under `history_conditions/tokenizer_kimi/`. `provenance.json` records every download URL, byte count and SHA-256. Only tokenizer assets were downloaded; no model weights or provider calls were used.

`kimi_count.py` reconstructs the published tiktoken vocabulary, regex and special-token mapping by parsing the pinned code as data. It does not import downloaded custom code. It renders the pinned Jinja template with sorted tool-schema dictionaries and JSON serialization matching the template wrapper. The fixed `execute_command` declaration comes from the source environment's published tool definition; there are no additional tools. Counts include this declaration, role markers, one visible reasoning representation per source assistant, tool-call IDs/arguments, tool observations and the assistant generation prefix. They exclude future generated tokens and unknown provider-side additions.

Every rendered string round-trips through the encoding. The strings are below the published tokenizer's chunking thresholds. The source's duplicated reasoning aliases and `reasoning_details` text are preserved in JSON where required but are not counted three times; the public template reads `reasoning_content`. The actual backend may transform these fields or use a different template, which remains unverified.

| Checkpoint | Condition | Messages | Roles | Local prompt tokens | B-only treatment tokens | Rendered characters | UTF-8 bytes |
|---|---|---:|---|---:|---:|---:|---:|
| 258_step42 | A_FULL | 88 | S,U,(A,T)×43 | 40451 | 0 | 167808 | 167818 |
| 258_step42 | A_FAITHFUL_COMPACT | 5 | S,U,A,A,T | 30777 | 0 | 119624 | 119634 |
| 258_step42 | B_EFFORT_HISTORY | 5 | S,U,A,A,T | 14379 | 24 | 60538 | 60544 |
| 258_step42 | C_CURRENT_STATE | 5 | S,U,A,A,T | 14355 | 0 | 60417 | 60423 |
| 108_step32 | A_FULL | 68 | S,U,(A,T)×33 | 35919 | 0 | 140724 | 140726 |
| 108_step32 | A_FAITHFUL_COMPACT | 5 | S,U,A,A,T | 26098 | 0 | 96328 | 96330 |
| 108_step32 | B_EFFORT_HISTORY | 5 | S,U,A,A,T | 13273 | 24 | 56310 | 56312 |
| 108_step32 | C_CURRENT_STATE | 5 | S,U,A,A,T | 13249 | 0 | 56189 | 56191 |

S=system, U=user, A=assistant, T=tool. Message counts exclude the tool declaration and generated-assistant prefix; token counts include their published-template framing. Treatment count is the literal B prefix including its blank line, without a separate role wrapper. Zero for other conditions means the B-only treatment is absent, not that those conditions lack history.

B−C is +24 local-template tokens and +121 ASCII characters/bytes at both checkpoints. No filler is used. A_FULL−A_FAITHFUL_COMPACT is 9,674 tokens at 258 and 9,821 at 108, reductions of approximately 23.9% and 27.3%. These are substantial context-length changes, even with all source reasoning and observations preserved. A_FAITHFUL_COMPACT remains 30,777/26,098 tokens; shortening it further would require a new semantic compression review.

Object hashes below use UTF-8 JSON with sorted keys, ensure_ascii=False and Python's default separators. Each manifest also records the prompt-content hashes, payload-file hash, rendering hash, tool schema, source cutoff, prose and code dependencies. Original prompt and final-pair objects remain identical within each checkpoint across all four conditions.

| Checkpoint | Condition | System object SHA-256 | User object SHA-256 | Final assistant/tool pair SHA-256 |
|---|---|---|---|---|
| 258_step42 | A_FULL | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `d908849663b5e0b0baf0cf887be5d05abc496a3e8b45c48f8c248d8eaddfb4e8` |
| 258_step42 | A_FAITHFUL_COMPACT | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `d908849663b5e0b0baf0cf887be5d05abc496a3e8b45c48f8c248d8eaddfb4e8` |
| 258_step42 | B_EFFORT_HISTORY | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `d908849663b5e0b0baf0cf887be5d05abc496a3e8b45c48f8c248d8eaddfb4e8` |
| 258_step42 | C_CURRENT_STATE | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `d908849663b5e0b0baf0cf887be5d05abc496a3e8b45c48f8c248d8eaddfb4e8` |
| 108_step32 | A_FULL | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `5b4f8d2099c44138d7fe8f539fa82fb5d939078b1761a4d11654e9ffe420dc79` |
| 108_step32 | A_FAITHFUL_COMPACT | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `5b4f8d2099c44138d7fe8f539fa82fb5d939078b1761a4d11654e9ffe420dc79` |
| 108_step32 | B_EFFORT_HISTORY | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `5b4f8d2099c44138d7fe8f539fa82fb5d939078b1761a4d11654e9ffe420dc79` |
| 108_step32 | C_CURRENT_STATE | `22d39fa39bbe7321301af193cfb3dabf76c3db25d224588d846b2d4380586bc0` | `d4778a6cfce0686474e48209841217cacfb26fc6818e95868fe7b001d4d593b9` | `5b4f8d2099c44138d7fe8f539fa82fb5d939078b1761a4d11654e9ffe420dc79` |
