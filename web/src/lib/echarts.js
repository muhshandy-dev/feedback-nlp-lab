import { BarChart, HeatmapChart, LineChart, ScatterChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent, VisualMapComponent, MarkLineComponent } from 'echarts/components';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([BarChart, HeatmapChart, LineChart, ScatterChart, GridComponent, LegendComponent, TooltipComponent, VisualMapComponent, MarkLineComponent, CanvasRenderer]);

export default echarts;
