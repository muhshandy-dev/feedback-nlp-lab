<script>
  import { onMount } from 'svelte';
  import echarts from '../lib/echarts.js';
  import { palette } from '../lib/format.js';

  // option: fungsi (warna) => opsi ECharts. label: deskripsi untuk pembaca layar.
  let { option, height = 280, label, theme = 'auto' } = $props();
  let el;
  let chart;

  function render() {
    if (!chart) return;
    const c = palette();
    const base = {
      animationDuration: 400,
      textStyle: { fontFamily: 'IBM Plex Sans, system-ui, sans-serif', color: c.ink },
      tooltip: { backgroundColor: c.surface, borderColor: c.line, textStyle: { color: c.ink } },
    };
    chart.setOption({ ...base, ...option(c), tooltip: { ...base.tooltip, ...(option(c).tooltip || {}) } }, true);
  }

  onMount(() => {
    chart = echarts.init(el, null, { renderer: 'canvas' });
    render();
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(el);
    const mq = matchMedia('(prefers-color-scheme: dark)');
    const onScheme = () => render();
    mq.addEventListener('change', onScheme);
    return () => {
      ro.disconnect();
      mq.removeEventListener('change', onScheme);
      chart.dispose();
    };
  });

  $effect(() => {
    option;
    theme;
    render();
  });
</script>

<div class="chart" bind:this={el} role="img" aria-label={label} style:height="{height}px"></div>

<style>
  .chart { width: 100%; min-width: 0; }
</style>
