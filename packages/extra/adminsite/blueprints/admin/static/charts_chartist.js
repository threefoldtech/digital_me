$(function(){var e=(new Chartist.Line(".ct-chart-line",{labels:["Monday","Tuesday","Wednesday","Thursday","Friday"],series:[[12,9,7,8,5],[2,1,3.5,7,3],[1,3,4,5,6]]},{fullWidth:!0,chartPadding:{right:40}}),new Chartist.Line(".ct-chart-line-area",{labels:[1,2,3,4,5,6,7,8],series:[[5,9,7,8,5,3,5,4]]},{low:0,showArea:!0}),new Chartist.Line(".ct-chart-bipolar",{labels:[1,2,3,4,5,6,7,8],series:[[1,2,3,1,-2,0,1,0],[-2,-1,-2,-1,-2.5,-1,-2,-1],[0,0,0,1,2,2.5,2,1],[2.5,2,1,.5,1,.5,-1,-2.5]]},{high:3,low:-3,showArea:!0,showLine:!1,showPoint:!1,fullWidth:!0,axisX:{showLabel:!1,showGrid:!1}}),{labels:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],series:[[5,4,3,7,5,10,3,4,8,10,6,8],[3,2,9,5,4,6,4,6,7,8,7,4]]}),a={seriesBarDistance:10},t=[["screen and (max-width: 640px)",{seriesBarDistance:5,axisX:{labelInterpolationFnc:function(e){return e[0]}}}]],r=(new Chartist.Bar(".ct-chart-bars",e,a,t),{series:[5,3,4]}),i=function(e,a){return e+a};new Chartist.Pie(".ct-chart-pie",r,{labelInterpolationFnc:function(e){return Math.round(e/r.series.reduce(i)*100)+"%"}});new Chartist.Pie(".ct-chart-gauge",{series:[20,10,30,40]},{donut:!0,donutWidth:60,startAngle:270,total:200,showLabel:!1})});