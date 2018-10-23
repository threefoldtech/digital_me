// Masonry
window.addEventListener('load', () => {
    if ($('.masonry').length > 0) {
        new Masonry('.masonry', {
            itemSelector: '.masonry-item',
            columnWidth: '.masonry-sizer',
            percentPosition: true,
        });
    }
});

// ------------------------------------------------------
// @Line Charts
// ------------------------------------------------------

const lineChartBox = document.getElementById('line-chart');

if (lineChartBox) {
    const lineCtx = lineChartBox.getContext('2d');
    lineChartBox.height = 80;

    new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
            datasets: [{
                label: 'Series A',
                backgroundColor: 'rgba(237, 231, 246, 0.5)',
                borderColor: COLORS['deep-purple-500'],
                pointBackgroundColor: COLORS['deep-purple-700'],
                borderWidth: 2,
                data: [60, 50, 70, 60, 50, 70, 60],
            }, {
                label: 'Series B',
                backgroundColor: 'rgba(232, 245, 233, 0.5)',
                borderColor: COLORS['blue-500'],
                pointBackgroundColor: COLORS['blue-700'],
                borderWidth: 2,
                data: [70, 75, 85, 70, 75, 85, 70],
            }],
        },

        options: {
            legend: {
                display: false,
            },
        },

    });
}

// ------------------------------------------------------
// @Bar Charts
// ------------------------------------------------------

const barChartBox = document.getElementById('bar-chart');

if (barChartBox) {
    const barCtx = barChartBox.getContext('2d');

    new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
            datasets: [{
                label: 'Dataset 1',
                backgroundColor: COLORS['deep-purple-500'],
                borderColor: COLORS['deep-purple-800'],
                borderWidth: 1,
                data: [10, 50, 20, 40, 60, 30, 70],
            }, {
                label: 'Dataset 2',
                backgroundColor: COLORS['light-blue-500'],
                borderColor: COLORS['light-blue-800'],
                borderWidth: 1,
                data: [10, 50, 20, 40, 60, 30, 70],
            }],
        },

        options: {
            responsive: true,
            legend: {
                position: 'bottom',
            },
        },
    });
}

// ------------------------------------------------------
// @Area Charts
// ------------------------------------------------------

const areaChartBox = document.getElementById('area-chart');

if (areaChartBox) {
    const areaCtx = areaChartBox.getContext('2d');

    new Chart(areaCtx, {
        type: 'line',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
            datasets: [{
                backgroundColor: 'rgba(3, 169, 244, 0.5)',
                borderColor: COLORS['light-blue-800'],
                data: [10, 50, 20, 40, 60, 30, 70],
                label: 'Dataset',
                fill: 'start',
            }],
        },
    });
}

// ------------------------------------------------------
// @Scatter Charts
// ------------------------------------------------------

const scatterChartBox = document.getElementById('scatter-chart');

if (scatterChartBox) {
    const scatterCtx = scatterChartBox.getContext('2d');

    Chart.Scatter(scatterCtx, {
        data: {
            datasets: [{
                label: 'My First dataset',
                borderColor: COLORS['red-500'],
                backgroundColor: COLORS['red-500'],
                data: [{
                        x: 10,
                        y: 20
                    },
                    {
                        x: 30,
                        y: 40
                    },
                    {
                        x: 50,
                        y: 60
                    },
                    {
                        x: 70,
                        y: 80
                    },
                    {
                        x: 90,
                        y: 100
                    },
                    {
                        x: 110,
                        y: 120
                    },
                    {
                        x: 130,
                        y: 140
                    },
                ],
            }, {
                label: 'My Second dataset',
                borderColor: COLORS['green-500'],
                backgroundColor: COLORS['green-500'],
                data: [{
                        x: 150,
                        y: 160
                    },
                    {
                        x: 170,
                        y: 180
                    },
                    {
                        x: 190,
                        y: 200
                    },
                    {
                        x: 210,
                        y: 220
                    },
                    {
                        x: 230,
                        y: 240
                    },
                    {
                        x: 250,
                        y: 260
                    },
                    {
                        x: 270,
                        y: 280
                    },
                ],
            }],
        },
    });
}

//   Easy-pie-chart
if ($('.easy-pie-chart').length > 0) {
    $('.easy-pie-chart').easyPieChart({
        onStep(from, to, percent) {
            this.el.children[0].innerHTML = `${Math.round(percent)} %`;
        },
    });
}

// ------------------------------------------------------
// @Dashboard Sparklines
// ------------------------------------------------------

const drawSparklines = () => {
    if ($('#sparklinedash').length > 0) {
        $('#sparklinedash').sparkline([0, 5, 6, 10, 9, 12, 4, 9], {
            type: 'bar',
            height: '20',
            barWidth: '3',
            resize: true,
            barSpacing: '3',
            barColor: '#4caf50',
        });
    }

    if ($('#sparklinedash2').length > 0) {
        $('#sparklinedash2').sparkline([0, 5, 6, 10, 9, 12, 4, 9], {
            type: 'bar',
            height: '20',
            barWidth: '3',
            resize: true,
            barSpacing: '3',
            barColor: '#9675ce',
        });
    }

    if ($('#sparklinedash3').length > 0) {
        $('#sparklinedash3').sparkline([0, 5, 6, 10, 9, 12, 4, 9], {
            type: 'bar',
            height: '20',
            barWidth: '3',
            resize: true,
            barSpacing: '3',
            barColor: '#03a9f3',
        });
    }

    if ($('#sparklinedash4').length > 0) {
        $('#sparklinedash4').sparkline([0, 5, 6, 10, 9, 12, 4, 9], {
            type: 'bar',
            height: '20',
            barWidth: '3',
            resize: true,
            barSpacing: '3',
            barColor: '#f96262',
        });
    }
};

drawSparklines();

// Redraw sparklines on resize
// $(window).resize(debounce(drawSparklines, 150));  ==> Need Fixs

// ------------------------------------------------------
// @Other Sparklines
// ------------------------------------------------------

$('#sparkline').sparkline(
    [5, 6, 7, 9, 9, 5, 3, 2, 2, 4, 6, 7], {
        type: 'line',
        resize: true,
        height: '20',
    }
);

$('#compositebar').sparkline(
    'html', {
        type: 'bar',
        resize: true,
        barColor: '#aaf',
        height: '20',
    }
);

$('#compositebar').sparkline(
    [4, 1, 5, 7, 9, 9, 8, 7, 6, 6, 4, 7, 8, 4, 3, 2, 2, 5, 6, 7], {
        composite: true,
        fillColor: false,
        lineColor: 'red',
        resize: true,
        height: '20',
    }
);

$('#normalline').sparkline(
    'html', {
        fillColor: false,
        normalRangeMin: -1,
        resize: true,
        normalRangeMax: 8,
        height: '20',
    }
);

$('.sparktristate').sparkline(
    'html', {
        type: 'tristate',
        resize: true,
        height: '20',
    }
);

$('.sparktristatecols').sparkline(
    'html', {
        type: 'tristate',
        colorMap: {
            '-2': '#fa7',
            resize: true,
            '2': '#44f',
            height: '20',
        },
    }
);

const values = [5, 4, 5, -2, 0, 3, -5, 6, 7, 9, 9, 5, -3, -2, 2, -4];
const valuesAlt = [1, 1, 0, 1, -1, -1, 1, -1, 0, 0, 1, 1];

$('.sparkline').sparkline(values, {
    type: 'line',
    barWidth: 4,
    barSpacing: 5,
    fillColor: '',
    lineColor: COLORS['red-500'],
    lineWidth: 2,
    spotRadius: 3,
    spotColor: COLORS['red-500'],
    maxSpotColor: COLORS['red-500'],
    minSpotColor: COLORS['red-500'],
    highlightSpotColor: COLORS['red-500'],
    highlightLineColor: '',
    tooltipSuffix: ' Bzzt',
    tooltipPrefix: 'Hello ',
    width: 100,
    height: undefined,
    barColor: '9f0',
    negBarColor: 'ff0',
    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

$('.sparkbar').sparkline(values, {
    type: 'bar',
    barWidth: 4,
    barSpacing: 1,
    fillColor: '',
    lineColor: COLORS['deep-purple-500'],
    tooltipSuffix: 'Celsius',
    width: 100,
    barColor: '39f',
    negBarColor: COLORS['deep-purple-500'],
    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

$('.sparktri').sparkline(valuesAlt, {
    type: 'tristate',
    barWidth: 4,
    barSpacing: 1,
    fillColor: '',
    lineColor: COLORS['light-blue-500'],
    tooltipSuffix: 'Celsius',
    width: 100,
    barColor: COLORS['light-blue-500'],
    posBarColor: COLORS['light-blue-500'],
    negBarColor: 'f90',
    zeroBarColor: '000',
    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

$('.sparkdisc').sparkline(values, {
    type: 'discrete',
    barWidth: 4,
    barSpacing: 5,
    fillColor: '',
    lineColor: '9f0',
    tooltipSuffix: 'Celsius',
    width: 100,
    barColor: '9f0',

    negBarColor: 'f90',

    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

$('.sparkbull').sparkline(values, {
    type: 'bullet',
    barWidth: 4,
    barSpacing: 5,
    fillColor: '',
    lineColor: COLORS['amber-500'],
    tooltipSuffix: 'Celsius',
    height: 'auto',
    width: 'auto',
    targetWidth: 'auto',
    barColor: COLORS['amber-500'],
    negBarColor: 'ff0',
    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

$('.sparkbox').sparkline(values, {
    type: 'box',
    barWidth: 4,
    barSpacing: 5,
    fillColor: '',
    lineColor: '9f0',
    tooltipSuffix: 'Celsius',
    width: 100,
    barColor: '9f0',
    negBarColor: 'ff0',
    stackedBarColor: ['ff0', '9f0', '999', 'f60'],
    sliceColors: ['ff0', '9f0', '000', 'f60'],
    offset: '30',
    borderWidth: 1,
    borderColor: '000',
});

// ------------------------------------------------------
// @Popover
// ------------------------------------------------------

$('[data-toggle="popover"]').popover();

// ------------------------------------------------------
// @Tooltips
// ------------------------------------------------------

$('[data-toggle="tooltip"]').tooltip();

//   Perfect Scrollbar
const scrollables = $('.scrollable');
if (scrollables.length > 0) {
    scrollables.each((index, el) => {
        new PerfectScrollbar(el);
    });
}

// Search
$('.search-toggle').on('click', e => {
    $('.search-box, .search-input').toggleClass('active');
    $('.search-input input').focus();
    e.preventDefault();
});

// Sidebar links
$('.sidebar .sidebar-menu li a').on('click', function () {
    const $this = $(this);

    if ($this.parent().hasClass('open')) {
        $this
            .parent()
            .children('.dropdown-menu')
            .slideUp(200, () => {
                $this.parent().removeClass('open');
            });
    } else {
        $this
            .parent()
            .parent()
            .children('li.open')
            .children('.dropdown-menu')
            .slideUp(200);

        $this
            .parent()
            .parent()
            .children('li.open')
            .children('a')
            .removeClass('open');

        $this
            .parent()
            .parent()
            .children('li.open')
            .removeClass('open');

        $this
            .parent()
            .children('.dropdown-menu')
            .slideDown(200, () => {
                $this.parent().addClass('open');
            });
    }
});

// Sidebar Activity Class
const sidebarLinks = $('.sidebar').find('.sidebar-link');

sidebarLinks
    .each((index, el) => {
        $(el).removeClass('active');
    })
    .filter(function () {
        const href = $(this).attr('href');
        const pattern = href[0] === '/' ? href.substr(1) : href;
        return pattern === (window.location.pathname).substr(1);
    })
    .addClass('active');

// ٍSidebar Toggle
$('.sidebar-toggle').on('click', e => {
    $('.app').toggleClass('is-collapsed');
    e.preventDefault();
});

/**
 * Wait untill sidebar fully toggled (animated in/out)
 * then trigger window resize event in order to recalculate
 * masonry layout widths and gutters.
 */
$('#sidebar-toggle').click(e => {
    e.preventDefault();
    setTimeout(() => {
        window.dispatchEvent(window.EVENT);
    }, 300);
});

// VectorMap

const vectorMapInit = (data, countryCodes) => {
    if ($('#world-map-marker').length > 0) {
        // This is a hack, as the .empty() did not do the work
        $('#vmap').remove();
        console.log(data)
        // we recreate (after removing it) the container div, to reset all the data of the map
        $('#world-map-marker').append(`
        <div
          id="vmap"
          style="
            height: 490px;
            position: relative;
            overflow: hidden;
            background-color: transparent;
          "
        >
        </div>
      `);

        $('#vmap').vectorMap({
            map: 'world_mill',
            backgroundColor: '#fff',
            borderColor: '#fff',
            borderOpacity: 0.25,
            borderWidth: 0,
            color: '#e6e6e6',
            regionStyle: {
                initial: {
                    fill: '#e4ecef',
                },
                selected: {
                    fill: 'blue'
                },
            },

            markerStyle: {
                initial: {
                    r: 7,
                    'fill': '#fff',
                    'fill-opacity': 1,
                    'stroke': '#000',
                    'stroke-width': 2,
                    'stroke-opacity': 0.4,
                },
            },

            markers: data,

            series: {
                regions: [{
                    values: countryCodes,
                    scale: ['#ff0000', '#0000ff'],
                    normalizeFunction: 'polynomial',
                }],
            },
            hoverOpacity: null,
            normalizeFunction: 'linear',
            zoomOnScroll: false,
            scaleColors: ['#b6d6ff', '#005ace'],
            selectedColor: '#000000',
            selectedRegions: countryCodes,
            enableZoom: false,
            hoverColor: '#fff',
        });

    }
};

// vectorMapInit();
// $(window).resize(debounce(vectorMapInit, 150));

// Datatable
$('#dataTable').DataTable();

// Bootstrap DatePicker
$('.start-date').datepicker();
$('.end-date').datepicker();

// Email
$('.email-side-toggle').on('click', e => {
    $('.email-app').toggleClass('side-active');
    e.preventDefault();
});

$('.email-list-item, .back-to-mailbox').on('click', e => {
    $('.email-content').toggleClass('open');
    e.preventDefault();
});

// ------------------------------------------------------
// @Window Resize
// ------------------------------------------------------

/**
 * NOTE: Register resize event for Masonry layout
 */
const EVENT = document.createEvent('UIEvents');
window.EVENT = EVENT;
EVENT.initUIEvent('resize', true, false, window, 0);


window.addEventListener('load', () => {
    /**
     * Trigger window resize event after page load
     * for recalculation of masonry layout.
     */
    window.dispatchEvent(EVENT);
});

// ------------------------------------------------------
// @External Links
// ------------------------------------------------------

// Open external links in new window
$('a')
    .filter('[href^="http"], [href^="//"]')
    .not(`[href*="${window.location.host}"]`)
    .attr('rel', 'noopener noreferrer')
    .attr('target', '_blank');

// ------------------------------------------------------
// @Resize Trigger
// ------------------------------------------------------

// Trigger resize on any element click
document.addEventListener('click', () => {
    window.dispatchEvent(window.EVENT);
});

function select_node(id) {
    location.href = "node/" + id
}