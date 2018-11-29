#!/usr/bin/python
# author: Jan Hybs

import os
import datetime
import time
import cihpc.common.utils.strings
import json

from cihpc.common.logging import logger


instrument_shell_pre = lambda output_file: '''
_MEASURE_START_TIME=`echo $(($(date +%s%N)/1000000))`
'''

instrument_shell_post = lambda output_file: '''
_MEASURE_END_TIME=`echo $(($(date +%s%N)/1000000))`
_MEASURE_ELAPSED_TIME=$(($_MEASURE_END_TIME - $_MEASURE_START_TIME))
echo $_MEASURE_ELAPSED_TIME > "{}"
'''.format(output_file)


def process_step_measure(step, measure, shell_processing):
    """
    Function will collect artifacts for the given step
    :type step:            cihpc.core.structures.project_step.ProjectStep
    :type measure:         ProjectStepMeasure
    :type shell_processing: ShellProcessing
    """
    if not measure:
        return

    if measure.type is not measure.Type.TYPE_INSTRUMENT_SHELL:
        return

    logger.info('measuring artifacts')

    kwargs = dict(
        datetime=datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'),
        timestamp=str(int(time.time())),
        random4=cihpc.common.utils.strings.generate_random_key(4),
    )

    instrument_output = os.path.join(
        step.measure.move_to,
        '{datetime}-{random4}.artifact'
    ).format(**kwargs)
    os.makedirs(os.path.dirname(instrument_output), 0o777, True)

    def before_shell(tmp_sh):
        """
        :type tmp_sh: files.temp_file.TempFile
        """
        tmp_sh.write_section('PRE-INSTRUMENT', instrument_shell_pre(instrument_output))

    def after_shell(tmp_sh):
        """
        :type tmp_sh: files.temp_file.TempFile
        """
        tmp_sh.write_section('POST-INSTRUMENT', instrument_shell_post(instrument_output))

    def read_measure(result):
        """
        :type result: proc.step.step_shell.ProcessStepResult
        """
        try:
            with open(instrument_output, 'r') as fp:
                result.shell_duration = float(fp.read().strip()) / 1000.0

            os.unlink(instrument_output)
            with open('%s.json' % instrument_output, 'w') as fp:
                json.dump({
                    'duration'          : result.shell_duration,
                    'container-duration': result.duration,
                }, fp)

        except:
            result.shell_duration = None

    shell_processing.shell.on_enter += before_shell,
    shell_processing.shell.on_exit += after_shell,
    shell_processing.process.on_exit += read_measure,

