import subprocess
import os
import time

def _parse_qstat_state(qstat_out, job_id):
    """Parse "state" column from `qstat` output for given job_id
    Returns state for the *first* job matching job_id. Returns 'u' if
    `qstat` output is empty or job_id is not found.
    """
    if qstat_out.strip() == '':
        return 'u'
    lines = qstat_out.split('\n')
    # skip past header
    while not lines.pop(0).startswith('---'):
        pass
    for line in lines:
        if line:
            job, prior, name, user, state = line.strip().split()[0:5]
            if int(job) == int(job_id):
                return state
    return 'u'


def _parse_qstat_nodes(qstat_out):
    if qstat_out.strip() == '':
        return {}
    lines = qstat_out.split('\n')
    # skip past header
    while not lines.pop(0).startswith('---'):
        pass
    nodes = {}
    for line in lines:
        if line:
            node = line.strip().split()[7]
            if node in nodes: 
                 nodes[node] = nodes[node]+1
            else:
                 nodes[node] = 1
    return nodes


def _parse_qsub_job_id(qsub_out):
    """Parse job id from qsub output string.
    Assume format:
        "Your job <job_id> ("<job_name>") has been submitted"
    """
    return int(qsub_out.split()[2])


def _count_jobs(qstat_out):
    if qstat_out.strip() == '':
        return 0
    lines = qstat_out.split('\n')
    # skip past header
    while not lines.pop(0).startswith('---'):
        pass
    count = 0
    for line in lines:
	if line:
            count +=1
    return count


def check_running_jobs (user, job_ids):
    cmd = "qstat -u %s" % user
    output = subprocess.check_output(cmd, shell=True)
    count = 0
    if len(job_ids) == 0: return count
    for job_id in job_ids:
        state = _parse_qstat_state(output, job_id)
        if state == 'r' or state == 'qw' :
            count +=1
        else:
            job_ids.remove(job_id)
    return count


def submit_job(script_name, script_dir):
    #cmd = "qsub $(for i in $(seq 2 6); do sed \"$(echo $i)q;d\" %s | rev | cut -d' ' -f 1,2 |rev ;done | tr '\n' ' ' ) /usr/bin/singularity exec -B /RAID3 -B /SCRATCH /RAID3/romed/singularity/output/paris_0-8-34_0-2_2019-02-13 %s/%s" % (script_name, script_dir, script_name)
    cmd = f"qsub {script_name}"
    output = subprocess.check_output(cmd, shell=True)
    print(cmd)
    print(output)
    job_id = _parse_qsub_job_id(output)
    return job_id


def get_scripts(prefix):
    script_names = []
    for root, dirs, files in os.walk(os.getcwd()):
	for name in files:
            if name.startswith(prefix):
		script_names.append(name)
    return script_names


if __name__ == "__main__":
    user = "dave"
    script_prefix = "qscript_Sedov_"
    max_job_count = 1

    sub_scripts = get_scripts(script_prefix)
    running_jobs = []

    while len(sub_scripts) > 0:
        running = check_running_jobs(user, running_jobs)
        print (running)
        if running < max_job_count:
	    running_jobs.append(submit_job(sub_scripts.pop(), os.getcwd()))
            time.sleep(10)
        else:
            time.sleep(180) 





