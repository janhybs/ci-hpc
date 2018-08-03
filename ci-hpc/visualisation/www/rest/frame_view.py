#!/bin/python3
# author: Jan Hybs

from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
from bson.objectid import ObjectId

from utils import  strings
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig
from visualisation.www.plot.highcharts import highcharts_frame_bar
from artifacts.collect.modules import unwind_reports


class FrameView(Resource):

    @Timer.decorate('TestView: get', logger.info)
    def get(self, project, ids):
        mongo = CIHPCMongo.get(project)
        config = ProjectConfig.get(project)

        if config.frame_view.id_prop == '_id':
            filters = {
                config.frame_view.id_prop: {
                    '$in': [ObjectId(x) for x in ids.split(',')]
                },
            }
        else:
            filters = {
                config.frame_view.id_prop: {
                    '$in': ids.split(',')
                },
            }

        items = unwind_reports(
            mongo.find_all(
                filters,
                config.frame_view.get_projection(),
            ),
            flatten='.',
            unwind_from=config.frame_view.unwind['from'],
            unwind_to=config.frame_view.unwind['to'],
        )
        df = pd.DataFrame(items)

        if df.empty:
            return dict(
                error='No data found',
                description='This usually means filters provided filtered out everything.'
        )

        # df['git-datetime'] = df['git-datetime'].apply(dateutils.long_format)
        result = highcharts_frame_bar(df, config)
        strings.to_json(result)
        return result

        # index = 0
        # for g, d in df.groupby('test-size'):
        #     clr = 'rgba({}, {}, {}, %f)'.format(*[int(x*255) for x in colors[index]])
        #
        #     if args.separate:
        #         result.append(dict(
        #             mesh=g,
        #             data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #         ))
        #     else:
        #         if not result:
        #             result.append(dict(
        #                 mesh=g,
        #                 data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #             ))
        #         else:
        #             r = highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #             result[0]['data']['series'].extend(r['series'])
        #     index += 1
