from container_test_base import Container
import docker
import unittest
import httplib
import time
import socket
import json
import tempfile
import atexit
import shutil
from logging.handlers import SysLogHandler
import logging
import os.path
import glob
import sys

# See: http://csl.sublevel3.org/post/python-syslog-client/
class Facility:
  "Syslog facilities"
  KERN, USER, MAIL, DAEMON, AUTH, SYSLOG, \
  LPR, NEWS, UUCP, CRON, AUTHPRIV, FTP = range(12)

  LOCAL0, LOCAL1, LOCAL2, LOCAL3, \
  LOCAL4, LOCAL5, LOCAL6, LOCAL7 = range(16, 24)


class Level:
  "Syslog levels"
  EMERG, ALERT, CRIT, ERR, \
  WARNING, NOTICE, INFO, DEBUG = range(8)


def send_log(host,facility,level,msg,sock=None):
    if not sock:
        sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s="<{l}>Jan 01 01:01:11 {msg}".format(l=level + facility*8, msg=msg)
    sock.sendto(s,(host,5140))

class TestBase(unittest.TestCase):
    _dirs=None

    @classmethod
    def _cleanup(cls):
        for d in cls._dirs:
            shutil.rmtree(d,ignore_errors=True)
        cls._dirs=[]

    def __init__(self,methodName='runTest', **container_args):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if TestBase._dirs is None:
            TestBase._dirs=[]
            #atexit.register(TestBase._cleanup)
        self.log_dir=tempfile.mkdtemp(prefix="unittest_rsyslog_logs")
        TestBase._dirs.append(self.log_dir)
        super(TestBase,self).__init__(methodName=methodName)
        self.rsyslog = Container(path='..')
        self.rsyslog.set_container_args(environment={'FLUENTD_OPT':'-vvv','with_syslog':'1','with_filesystem':'1','with_debug':'1','immediate':'1'},
                                        volumes={self.log_dir:{'bind': '/fluentd/log', 'mode': 'rw'} },
                                        **container_args)

    def assert_file_content(self,log_glob,content=None,negate=False):
        logs = glob.glob(self.log_dir+"/"+log_glob)
        self.assertEquals(len(logs),1)
        if content:
            f = file(logs[0])
            if negate:
                self.assertFalse(content in f.read())
            else:
                self.assertTrue(content in f.read())
            f.close()
        

class StandardConfigTest(TestBase):

    def __init__(self,methodName='runTest'):
        super(StandardConfigTest,self).__init__(methodName=methodName) 
        
                                               
    def testSimpleMsg(self):
        send_log(self.rsyslog.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::HERE::",
            sock=self.socket)
        time.sleep(5)
        print str(glob.glob(self.log_dir+"/*"))
        print str(glob.glob(self.log_dir+"/by_host/*/*"))
        #print self.rsyslog.container.logs(stdout=True,stderr=True)
        self.assert_file_content("by_host/localhost/daemon-fluent.*")
        self.assert_file_content("by_host/thehost/user-theapp.*","::HERE::")

class ForwardingTest(TestBase):

    def __init__(self,methodName='runTest'):
        super(ForwardingTest,self).__init__(methodName=methodName)
        self.fwd=Container(path='..')
        environment={'FLUENTD_OPT':'-vvv','with_forward':self.rsyslog.ip_address,'with_syslog':'1','with_debug':'1','immediate':'1'}

        self.fwd.set_container_args(environment=environment)
        docker.DockerClient().containers.run
        
                                               
    def testFwdFail(self):
        send_log(self.fwd.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::BEFORE::",
            sock=self.socket)
        time.sleep(20)
        print self.fwd.container.logs(stdout=True,stderr=True)
        print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        print self.rsyslog.container.logs(stdout=True,stderr=True)
        print str(glob.glob(self.log_dir+"/by_host/*"))
        print str(glob.glob(self.log_dir+"/by_host/*/*"))
        self.assert_file_content("by_host/thehost/user-theapp.*","::BEFORE::")

        print "stopping sink"
        self.rsyslog.container.stop()
        send_log(self.fwd.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::DELAYED::",
            sock=self.socket)
        time.sleep(2)

        self.assert_file_content("by_host/thehost/user-theapp.*","::DELAYED::",negate=True)

        send_log(self.fwd.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::DELAYED2::",
            sock=self.socket)
        time.sleep(2)

        print "starting sink again"
        self.rsyslog.container.start()
        self.rsyslog.container.reload()
        time.sleep(2)
        send_log(self.fwd.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::AFTER::",
            sock=self.socket)
        send_log(self.fwd.ip_address,Facility.USER,Level.INFO,"thehost theapp[111]:the message is ::AFTER2::",
            sock=self.socket)
        time.sleep(20)
        #print file(logfile).read()
        print self.fwd.container.logs(stdout=True,stderr=True)
        #print "enter"
        #sys.stdin.readline()
        self.assert_file_content("by_host/thehost/user-theapp.*","::AFTER::")
        self.assert_file_content("by_host/thehost/user-theapp.*","::AFTER2::")
        self.assert_file_content("by_host/thehost/user-theapp.*","::DELAYED2::")
        self.assert_file_content("by_host/thehost/user-theapp.*","::DELAYED::")

if __name__ == '__main__':
    unittest.main()
