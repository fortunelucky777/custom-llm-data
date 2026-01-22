<script>
	import katex from 'katex';

	export let math;
	export let displayMode = false;
	export let style;

	const options = {
		displayMode,
		throwOnError: false,
		style
	};

	$: katexString = katex.renderToString(math, options);
</script>

<svelte:head>
	<link
		rel="stylesheet"
		href="/katex/katex.min.css"
		crossorigin="anonymous"
	/>
</svelte:head>

{@html katexString}
