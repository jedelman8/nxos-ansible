#!usr/bin/env python


from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils
import json
import os
import time
import sys

utils.VERBOSITY = 1
stats = callbacks.AggregateStats()
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

TEST_PLAYBOOK_DIR = 'test-playbooks'
MODULE_DIR = 'library'
INVENTORY_FILE = 'test_inventory'


if __name__ == "__main__":

    for test_playbook_filename in os.listdir(TEST_PLAYBOOK_DIR):
        if '.yml' in test_playbook_filename:
            print 'Testing: ', test_playbook_filename

            pb_with_full_path = os.path.join(TEST_PLAYBOOK_DIR,
                                             test_playbook_filename)

            pb = PlayBook(
               transport='local',
               playbook=pb_with_full_path,
               host_list=INVENTORY_FILE,
               callbacks=playbook_cb,
               runner_callbacks=runner_cb,
               stats=stats,
            )

            results = pb.run()

            print json.dumps(results, indent=4)

            for device, results in results.items():
                if results.get('failures') > 0:
                    print '-------------------------------'
                    print 'TEST FAILURE'
                    print '-------------------------------'
                    sys.exit(1)

            print '=' * 40
            print '=' * 40
            print '=' * 40
            print '=' * 40
            print '=' * 40

            # Adding timer to give the API some R&R
            time.sleep(10)

    print '-------------------------------'
    print 'Successfully Completed Testing.'
    print '-------------------------------'
    sys.exit(0)
