"""The re-invocation check must fail on a replacement or a failed consumer."""
import unittest
from qualify_hq_postgrest import verify_no_second_effect

BEFORE={'mission':['a'*64],'gateway':['b'*64]}


def check(**changes):
    call={'label':'fixture','before':BEFORE,'after':dict(BEFORE),'exit_code':0,
          'expected_exit':0,'reported_jobs':0,'stderr':''}
    return verify_no_second_effect(**{**call,**changes})


class ReinvocationCheckTests(unittest.TestCase):
    def test_unchanged_identities_and_clean_exit_are_accepted(self):
        verdict=check()
        self.assertTrue(verdict['identitiesUnchanged'])
        self.assertEqual(verdict['missionContainerIds'],BEFORE['mission'])
        self.assertEqual(verdict['gatewayContainerIds'],BEFORE['gateway'])
        self.assertEqual(verdict['reinvocationExit'],0)

    def test_replacement_extra_container_failure_or_new_work_is_detected(self):
        cases=[('mission identity changed',{'after':{'mission':['c'*64],'gateway':['b'*64]}}),
               ('gateway identity changed',{'after':{'mission':['a'*64],'gateway':['d'*64]}}),
               ('mission identity changed',{'after':{'mission':['a'*64,'c'*64],'gateway':['b'*64]}}),
               ('mission has 2 containers',{'before':{'mission':['a'*64,'c'*64],'gateway':['b'*64]},
                                            'after':{'mission':['a'*64,'c'*64],'gateway':['b'*64]}}),
               ('mission identity changed',{'after':{'mission':[],'gateway':['b'*64]}}),
               ("exit 2 instead of 0",{'exit_code':2}),
               ("consumer reported 1 job(s)",{'reported_jobs':1})]
        for expected,change in cases:
            with self.assertRaises(AssertionError) as raised:check(**change)
            self.assertIn(expected,str(raised.exception),change)

    def test_failure_diagnostic_keeps_the_stderr_tail(self):
        with self.assertRaises(AssertionError) as raised:
            check(exit_code=2,stderr='first line\nsecond line')
        message=str(raised.exception)
        self.assertIn('stderr tail:',message)
        self.assertIn('second line',message)


if __name__=='__main__':unittest.main()
