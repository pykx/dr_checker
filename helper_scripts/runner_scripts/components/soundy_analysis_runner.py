from base_component import *
import os
import argparse
from multiprocessing import Pool, cpu_count
import tempfile

# For optional profiling flag
profiling_subdir = "prof"
profiling_prefix_start = "LD_PRELOAD=" + os.path.join(*[os.sep, 'usr','lib','libprofiler.so']) + " CPUPROFILE="

class SoundyAnalysisRunner(Component):
    """
        Component which tries to run Soundy Analysis on all the provided entry points.
    """

    def __init__(self, value_dict):
        soundy_analysis_so = None
        entry_point_out = None
        soundy_analysis_out = None
        opt_bin_path = None
        soundy_analysis_instr_out = None
        profiling_enabled = False
        if 'soundy_analysis_so' in value_dict:
            soundy_analysis_so = value_dict['soundy_analysis_so']
        if 'entry_point_out' in value_dict:
            entry_point_out = value_dict['entry_point_out']
        if 'soundy_analysis_out' in value_dict:
            soundy_analysis_out = value_dict['soundy_analysis_out']
        if 'soundy_analysis_instr_out' in value_dict:
            soundy_analysis_instr_out = value_dict['soundy_analysis_instr_out']
        if 'opt_bin_path' in value_dict:
            opt_bin_path = value_dict['opt_bin_path']
        if 'soundy_analysis_profiling_enabled' in value_dict:
            profiling_enabled = value_dict['soundy_analysis_profiling_enabled']

        self.opt_bin_path = opt_bin_path
        self.soundy_analysis_so = soundy_analysis_so
        self.entry_point_out = entry_point_out
        self.soundy_analysis_out = soundy_analysis_out
        self.soundy_analysis_instr_out = soundy_analysis_instr_out
        self.profiling_enabled = profiling_enabled

    def setup(self):
        if not os.path.exists(self.soundy_analysis_so):
            return "Provided Soundy Analysis so path:" + str(self.soundy_analysis_so) + " does not exist."
        if not os.path.exists(self.opt_bin_path):
            return "Provided opt bin path:" + str(self.opt_bin_path) + " does not exist."
        if not os.path.exists(self.entry_point_out):
            return "Provided entry point out file path:" + str(self.entry_point_out) + " is invalid."
        if self.soundy_analysis_out is None:
            return "Provided Soundy Analysis out folder path:" + str(self.soundy_analysis_out) + " is invalid."
        # set up the directory if this is not present.
        if not os.path.isdir(self.soundy_analysis_out):
            os.system('mkdir -p ' + self.soundy_analysis_out)
        if not os.path.isdir(self.soundy_analysis_instr_out):
            os.system('mkdir -p ' + self.soundy_analysis_instr_out)
        if self.profiling_enabled:
            if not os.path.isdir(os.path.join(self.soundy_analysis_out, profiling_subdir)):
                os.system('mkdir -p ' + os.path.join(self.soundy_analysis_out, profiling_subdir))

        return None

    def perform(self):
        log_info("Invoking Soundy Checker")
        return _run_multi_soundy_checker(self.entry_point_out, self.opt_bin_path, self.soundy_analysis_so,
                                         self.soundy_analysis_out, self.soundy_analysis_instr_out, 
                                         self.profiling_enabled)

    def get_name(self):
        return "SoundyAnalysisRunner"

    def is_critical(self):
        # Yes, this component is critical.
        return True


def setup_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', action='store', dest='entry_point_out',
                        help='Path to the entry point output file.')

    parser.add_argument('-p', action='store', dest='opt_bin_path',
                        help='Path to the opt executable.')

    parser.add_argument('-s', action='store', dest='soundy_analysis_so',
                        help='Path to the Soundy Analysis Pass shared object (so).')

    parser.add_argument('-f', action='store', dest='soundy_analysis_out',
                        help='Path to the output folder where the Soundy Checker output should be stored.')

    parser.add_argument('-ap', action='store_true', dest='run_soundy_with_profiling_enabled', default=False,
                        help='Run Soundy Analysis with performance profiling enabled (default: no performance profiling).')

    return parser


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()
    arg_dict = dict()
    arg_dict['opt_bin_path'] = parsed_args.opt_bin_path
    arg_dict['soundy_analysis_so'] = parsed_args.soundy_analysis_so
    arg_dict['soundy_analysis_out'] = parsed_args.soundy_analysis_out
    arg_dict['entry_point_out'] = parsed_args.entry_point_out
    arg_dict['soundy_analysis_instr_out'] = os.path.join(parsed_args.soundy_analysis_out, "instr_warnings")
    if parsed_args.run_soundy_with_profiling_enabled:
        arg_dict['soundy_analysis_profiling_enabled'] = True
    soundy_runner = SoundyAnalysisRunner(arg_dict)
    setup_msg = soundy_runner.setup()
    if setup_msg is not None:
        log_error("Component:", soundy_runner.get_name(), " setup failed with msg:", setup_msg)


def _run_soundy_checker(combined_arg):
    TIMEOUT_IN_MIN = "45"
    profiling_prefix = ""
    opt_bin_path = combined_arg[0]
    so_path = combined_arg[1]
    func_name = combined_arg[2]
    llvm_bc_file = combined_arg[3]
    output_json_file = combined_arg[4]
    instr_json_file = combined_arg[5]
    output_total_file = combined_arg[6]
    ep_type = combined_arg[7]
    out_path = combined_arg[8]
    enable_profiling = combined_arg[9]
    temp_bc_file = tempfile.NamedTemporaryFile(delete=False)
    bc_file_name = temp_bc_file.name
    temp_bc_file.close()

    # run mem2reg
    ret_val = os.system(opt_bin_path + " -mem2reg " + llvm_bc_file + " -o " + bc_file_name)
    if ret_val != 0:
        log_error("LLVM mem2reg failed on:", llvm_bc_file, " for function:", func_name,
                  ", So the output you get may be wrong.")

    # Add profiling prefix if requested
    if (enable_profiling):
        profiling_prefix = profiling_prefix_start + os.path.join(*[out_path, profiling_subdir, (str(func_name) + ".prof")]) + " " 

    timeout_prefix = 'timeout ' + TIMEOUT_IN_MIN + "m "
    ret_val = os.system(profiling_prefix + timeout_prefix + opt_bin_path + " -analyze -debug -load \"" + so_path + '\" '
                        + '-dr_checker -toCheckFunction=\"' + str(func_name) + '\" '
                        + '-functionType=\"' + ep_type + '\" '
                        + '-skipInit=1 -outputFile=\"' + output_json_file + '\" '
                        + '-instrWarnOutput=\"' + instr_json_file + '\" '
                        + bc_file_name + ' >> ' + output_total_file + ' 2>&1')
    return ret_val, func_name


def _run_multi_soundy_checker(entry_point_out, opt_bin_path, soundy_pass_so,
                              soundy_analysis_out, soundy_analysis_instr_out,
                              soundy_analysis_profiling_enabled):

    to_run_cmds = []
    fp = open(entry_point_out, 'r')
    all_lines = fp.readlines()
    fp.close()
    processed_func = []
    for curr_ep in all_lines:
        curr_ep = curr_ep.strip()
        all_p = curr_ep.split(':')
        if all_p[1] not in processed_func and all_p[0].strip() != "DEVSHOW":
            processed_func.append(all_p[1])
            to_run_cmds.append((opt_bin_path, soundy_pass_so, all_p[1], all_p[2],
                                os.path.join(soundy_analysis_out, all_p[1] + '.json'),
                                os.path.join(soundy_analysis_instr_out, all_p[1] + 'instr_warngs.json'),
                                os.path.join(soundy_analysis_out, all_p[1] + '.output'), 
                                all_p[0],
                                soundy_analysis_out,
                                soundy_analysis_profiling_enabled))

    log_info("Found:", len(to_run_cmds), " entry points to process.")
    log_info("Processing in multiprocessing mode")
    p = Pool(cpu_count())
    return_vals = p.map(_run_soundy_checker, to_run_cmds)
    log_info("Finished processing:", len(to_run_cmds), " entry points.")
    total_failed = 0
    for curr_r_val in return_vals:
        if int(curr_r_val[0]) != 0:
            total_failed += 1
            log_error("Soundy Analysis failed for:", curr_r_val[-1])
    log_info("Soundy Analysis failed for:", total_failed, " out of:", len(to_run_cmds), " entry points.")
    return True


if __name__ == "__main__":
    main()
