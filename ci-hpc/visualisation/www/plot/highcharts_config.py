

class Undefined(object): pass


undefined = Undefined()


class HighchartsObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_json(self):
        return {k:v for k, v in self.__dict__.items() if not isinstance(v, Undefined)}


class HighchartsChart(HighchartsObject):
    """
    :type zoomType: str
    """

    ZOOM_TYPE_XY = 'xy'
    ZOOM_TYPE_X = 'x'
    ZOOM_TYPE_Y = 'y'


    TYPE_AREA_RANGE = 'arearange'
    TYPE_AREA_SPLINE_RANGE = 'areasplinerange'
    TYPE_LINE = 'line'
    TYPE_SPLINE = 'spline'

    DASH_SOLID = 'solid'
    DASH_DASH = 'dash'

    AXIS_TYPE_LINEAR = 'linear'
    AXIS_TYPE_DATETIME = 'datetime'

    def __init__(self, **kwargs):
        self.zoomType = HighchartsChart.ZOOM_TYPE_XY
        super(HighchartsChart, self).__init__(**kwargs)


class HighchartsAxis(HighchartsObject):
    """
    :type title: HighchartsTitle
    :type categories: list[str]
    :type type: str
    """

    def __init__(self, **kwargs):
        self.title = HighchartsTitle(text=undefined)
        self.categories = undefined
        self.type = undefined
        super(HighchartsAxis, self).__init__(**kwargs)


class HighchartsPoint(HighchartsObject):
    """
    :type events: dict
    """

    def __init__(self, **kwargs):
        self.events = dict()
        super(HighchartsPoint, self).__init__(**kwargs)


class HighchartsMarker(HighchartsObject):
    """
    :type enabled: bool
    """

    def __init__(self, **kwargs):
        self.enabled = undefined
        super(HighchartsMarker, self).__init__(**kwargs)


class HighchartsTooltip(HighchartsObject):
    """
    :type shared: bool
    :type useHTML: bool
    :type crosshairs: bool
    :type followPointer: bool
    :type pointFormat: str
    """

    def __init__(self, **kwargs):
        self.shared = True
        self.useHTML = True
        self.crosshairs = True
        self.followPointer = True
        self.pointFormat = undefined
        super(HighchartsTooltip, self).__init__(**kwargs)


class HighchartsSeries(HighchartsObject):
    """
    :type type: str
    :type name: str
    :type data: dict
    :type commits: list[str]
    :type uuids: list[str]

    :type color: str
    :type fillColor: str
    :type dashStyle: str

    :type zIndex: int
    :type allowPointSelect: bool

    :type marker: HighchartsPoint
    :type point: HighchartsMarker
    """

    def __init__(self, **kwargs):
        self.type = HighchartsChart.TYPE_SPLINE
        self.name = undefined
        self.data = undefined
        self.commits = undefined
        self.uuids = undefined

        self.color = undefined
        self.fillColor = undefined
        self.dashStyle = undefined

        self.zIndex = undefined
        self.allowPointSelect = undefined

        self.point = HighchartsPoint()
        self.marker = HighchartsMarker()
        super(HighchartsSeries, self).__init__(**kwargs)


class HighchartsTitle(HighchartsObject):
    """
    :type text: str
    :type align: str
    :type x: int
    :type y: int
    """

    def __init__(self, **kwargs):
        self.text = 'duration [sec]'
        self.align = undefined
        self.x = undefined
        self.y = undefined
        super(HighchartsTitle, self).__init__(**kwargs)


class HighchartsLegend(HighchartsObject):
    """
    :type layout: str
    :type align: str
    :type verticalAlign: str
    """

    def __init__(self, **kwargs):
        self.layout = 'vertical'
        self.align = 'right'
        self.verticalAlign = 'middle'
        super(HighchartsLegend, self).__init__(**kwargs)


class HighchartsConfig(HighchartsObject):
    """
    :type chart: HighchartsChart
    :type title: HighchartsTitle
    :type yAxis: HighchartsAxis
    :type xAxis: HighchartsAxis
    :type legend: HighchartsLegend
    :type tooltip: HighchartsTooltip
    :type series: list[HighchartsSeries]

    """

    def __init__(self, **kwargs):
        self.chart = HighchartsChart()
        self.title = HighchartsTitle()
        self.yAxis = HighchartsAxis()
        self.xAxis = HighchartsAxis()
        self.legend = undefined
        self.tooltip = HighchartsTooltip()
        self.series = list()

        super(HighchartsConfig, self).__init__(**kwargs)

    def add(self, series):
        """
        :type series: HighchartsSeries
        """
        self.series.append(series)

