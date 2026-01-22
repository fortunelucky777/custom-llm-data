---
base_model: gpt2
library_name: transformers.js
---

https://huggingface.co/gpt2 with ONNX weights to be compatible with Transformers.js.

## Usage (Transformers.js)

If you haven't already, you can install the [Transformers.js](https://huggingface.co/docs/transformers.js) JavaScript library from [NPM](https://www.npmjs.com/package/@huggingface/transformers) using:
```bash
npm i @huggingface/transformers
```

You can then use the model to generate text as follows:

```js
import { pipeline } from '@huggingface/transformers';

// Create a text-generation pipeline
const generator = await pipeline('text-generation', 'Xenova/gpt2');

// Generate text (default parameters)
const text = 'Once upon a time,';
const output = await generator(text);
console.log(output);
// [{ generated_text: 'Once upon a time, I was in a room with a woman who was very attractive. She was' }]

// Generate text (custom parameters)
const output2 = await generator(text, {
    max_new_tokens: 20,
    do_sample: true,
    top_k: 5,
});
console.log(output2);
// [{ generated_text: 'generated_text: 'Once upon a time, the first thing I did was put a small piece of paper on a table. I put the paper' }]
```

Note: Having a separate repo for ONNX weights is intended to be a temporary solution until WebML gains more traction. If you would like to make your models web-ready, we recommend converting to ONNX using [🤗 Optimum](https://huggingface.co/docs/optimum/index) and structuring your repo like this one (with ONNX weights located in a subfolder named `onnx`).