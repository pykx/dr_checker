import argparse
import multiprocessing
import os
import time
import json
import sys
import matplotlib.pyplot as plt
import itertools

def log_info(*args):
    log_str = "[*] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print log_str


def log_error(*args):
    log_str = "[!] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print log_str


def log_warning(*args):
    log_str = "[?] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print log_str


def log_success(*args):
    log_str = "[+] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print log_str


def setup_args():
    parser = argparse.ArgumentParser(description="Script that converts DR.CHECKER LLVM based jsons to jsons "
                                                 "containing source code info.")

    parser.add_argument('-d', action='store', dest='dr_jsons',
                        help='Destination directory where all the DR.CHECKER jsons should be read from.')

    return parser


def process_json(src_json, runtime_list, pt_src_list, pt_dst_list, aa_src_list, aa_dst_list):
    """
        Process the json

    :return: None
    """
    fp = open(src_json, "r")
    fp_cont = fp.read()
    fp.close()
    if len(fp_cont) > 0:
        json_obj = json.loads(fp_cont)
        runtime_list.append(json_obj['runtime_in_secs'])
        pt_src_list.append(json_obj['points_to_summary'][0]['src_ptrs'])
        pt_dst_list.append(json_obj['points_to_summary'][1]['dst_ptrs'])
        aa_src_list.append(json_obj['alias_analysis_summary'][0]['src_ptrs'])
        aa_dst_list.append(json_obj['alias_analysis_summary'][1]['dst_ptrs'])

def usage():
    log_error("Invalid Usage.")
    log_error("Run: python ", __file__, "--help", ", to know the correct usage.")
    sys.exit(-1)


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()

    # check usage
    if parsed_args.dr_jsons is None:
        usage()

    log_info("Provided DR.CHECKER json dir:", parsed_args.dr_jsons)

    #all_tasks = []
    runtime_list = []
    pt_src_list = []
    pt_dst_list = []
    aa_src_list = []
    aa_dst_list = []
    for curr_json in os.listdir(parsed_args.dr_jsons):
        c_fp = os.path.join(parsed_args.dr_jsons, curr_json)
        if os.path.isfile(c_fp) and curr_json.endswith("stats.json"):
            process_json(c_fp, runtime_list, pt_src_list, pt_dst_list, aa_src_list, aa_dst_list)
            #all_tasks.append((c_fp))


    # Sort on runtime
    lists = sorted(itertools.izip(*[runtime_list, pt_dst_list, pt_src_list, aa_src_list, aa_src_list]))
    sorted_runtime_list, sorted_pt_dst_list, sorted_pt_src_list, sorted_aa_src_list, sorted_aa_dst_list = list(itertools.izip(*lists))
 
    plt.figure(1)
    plt.plot(sorted_runtime_list, sorted_pt_dst_list, color='red', label='pt_dst')
    plt.plot(sorted_runtime_list, sorted_pt_src_list, color='orange', label='pt_src')
    plt.xlabel('Runtime (seconds)')
    plt.ylabel('Points-To Ptr Count (No Alias Analysis)')
    plt.title('Ptr Count vs Runtime')
    plt.legend()

    plt.figure(2)
    plt.plot(sorted_runtime_list, sorted_aa_dst_list, color='green', label='aa_dst')
    plt.plot(sorted_runtime_list, sorted_aa_src_list, color='blue', label='aa_src')
    plt.xlabel('Runtime (seconds)')
    plt.ylabel('Corrected Points-To Ptr Count (After Alias Analysis)')
    plt.title('Ptr Count vs Runtime')
    plt.legend()

    plt.show()


    #log_info("Processing all jsons:", len(all_tasks), " in multiprocessing mode")
    #p = multiprocessing.Pool()
    #st = time.time()
    #p.map(process_json, all_tasks)
    #et = time.time() - st
    #log_info("Total time:", et, " seconds.")


if __name__ == "__main__":
    main()
