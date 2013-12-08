import os
import unittest
import fixtures
import testtools
import random

from connections import ContrailConnections
from contrail_test_init import ContrailTestInit
from tcutils.wrappers import preposttest_wrapper

from vpc_fixture_new import VPCFixture
from vpc_vn_fixture import VPCVNFixture
from vpc_vm_fixture import VPCVMFixture
from vpc_fip_fixture import VPCFIPFixture
from vn_test import *
from ec2_base import EC2Base
from testresources import ResourcedTestCase
from vpc_resource import VPCTestSetupResource
from vm_test import VMFixture
from project_test import ProjectFixture

sys.path.append(os.path.realpath('tcutils/pkgs/Traffic'))
from traffic.core.stream import Stream
from traffic.core.profile import create, ContinuousProfile,StandardProfile, BurstProfile
from traffic.core.helpers import Host
from traffic.core.helpers import Sender, Receiver

class VPCSanityTests(testtools.TestCase, ResourcedTestCase, fixtures.TestWithFixtures):
    """Tests for Euca2ools -> Amazon VPC support in Openstack Grizzly release """
    
    resources = [('base_setup', VPCTestSetupResource)]
    def __init__(self, *args, **kwargs):
        testtools.TestCase.__init__(self, *args, **kwargs)
        self.res= VPCTestSetupResource.getResource()
        self.inputs= self.res.inputs
        self.connections= self.res.connections
        self.vnc_lib = self.res.vnc_lib
        self.logger= self.res.logger
        self.nova_fixture= self.res.nova_fixture

    def __del__(self):
        print "Deleting vpc_test_with_setup now"
        VPCTestSetupResource.finishedWith(self.res)

    def setUp(self):
        super(VPCSanityTests, self).setUp()  
        if 'PARAMS_FILE' in os.environ :
            self.ini_file = os.environ.get('PARAMS_FILE')
        else:
            self.ini_file = 'params.ini'
        self.inputs = self.useFixture(ContrailTestInit(self.ini_file))
        self.connections = ContrailConnections(self.inputs)        
        self.quantum_fixture = self.connections.quantum_fixture
        self.nova_fixture = self.connections.nova_fixture
        self.agent_inspect_h = self.connections.agent_inspect
        self.logger = self.inputs.logger
    #end setUp
    
    def cleanUp(self):
        self.logger.info("Cleaning up")
        super(VPCSanityTests, self).cleanUp()
    # end cleanUp

    def runInstance(self):
        if not self.vpc.run_instance():
            self.logger.warn('run instance failed')
            return False
        return True
    # end runInstance

    def verifyInstance(self):
        if not self.vpc.verify_instance():
            self.logger.warn('verify instance failed')
            return False
        return True
    # end verifyInstance

    def allocateFloatingIp(self):
        if not self.vpc.allocate_floating_ip():
            self.logger.warn('allocate_floating_ip failed')
            return False
        return True
    # end allocateFloatingIp

    def associateFloatingIp(self):
        if not self.vpc.associate_floating_ip():
            self.logger.warn('associate_floating_ip failed')
            return False
        return True
    # end associateFloatingIp

    def disassociateFloatingIp(self):
        if not self.vpc.disassociate_floating_ip():
            self.logger.warn('associate_floating_ip failed')
            return False
        return True
    # end disassociateFloatingIp

    def verifyFloatingIp(self):
        if not self.vpc.verify_floating_ip():
            self.logger.warn('verify_floating_ip failed')
            return False
        return True
    # end verifyFloatingIp

    def createAcl(self,vpc_fixture):
        acl_id = vpc_fixture.create_acl()
        if not acl_id:
            self.logger.warn('create_network_acl failed')
            return None
        return acl_id
    # end createAcl

    def verifyAclBinding(self,vpc_vn_fixture, acl_id):
        if not vpc_vn_fixture.verify_acl_binding(acl_id):
            self.logger.warn('verify_network_acl %s failed' % (acl_id))
            return False
        return True
    # end verifyAclBinding

    def associateAcl(self, vpc_fixture, subnet_id, defAcl=None):
        if not vpc_fixture.associate_acl(subnet_id, defAcl):
            self.logger.warn('verify_network_acl failed')
            return False
        return True
    # end associateAcl

    def createAclRule(self, vpc_fixture, acl_id, rule):
        if not vpc_fixture.create_acl_rule(acl_id, rule):
            self.logger.warn('add_acl_rule failed')
            return False
        return True
    # end createAclRule

    def replaceAclRule(self, vpc_fixture, acl_id, rule):
        if not vpc_fixture.replace_acl_rule(acl_id, rule):
            self.logger.warn('replace_acl_rule failed')
            return False
        return True
    # end replaceAclRule

    def deleteAclRule(self, vpc_fixture, acl_id, rule):
        if not vpc_fixture.delete_acl_rule(acl_id, rule):
            self.logger.warn('delete_acl_rule failed')
            return False
        return True
    # end deleteAclRule

    def createSecurityGroup(self, vpc_fixture, sg_name):
        sg_id = vpc_fixture.create_security_group(sg_name)
        if not sg_id:
            self.logger.warn('create_security_group of %s failed' %(sg_name))
            return None
        return sg_id
    # end createSecurityGroup
    
    def deleteSecurityGroup(self, vpc_fixture, sg_id):
        if not vpc_fixture.delete_security_group(sg_id):
            self.logger.warn('delete_security_group of %s failed' %(sg_id))
            return False
        return True
    # end deleteSecurityGroup

    def verifySecurityGroup(self, vpc_fixture, sg_name):
        if not vpc_fixture.verify_security_group(sg_name):
            self.logger.warn('verify_security_group of %s failed' %(sg_name))
            return False
        return True
    # end verifySecurityGroup

    def createSgRule(self, vpc_fixture, sg_id, rule):
        if not vpc_fixture.create_security_group_rule(sg_id, rule):
            self.logger.warn('create_security_group_rule failed for SG ID %s' %(sg_id))
            return False
        return True
    # end createSgRule

    def deleteSgRule(self, vpc_fixture, sg_id, rule):
        if not vpc_fixture.delete_security_group_rule(sg_id,rule):
            self.logger.debug('delete_security_group_rule failed for SG ID %s' %(sg_id))
            return False
        return True
    # end deleteSgRule

    @preposttest_wrapper
    def test_create_delete_vpc(self):
        """Validate create VPC """
        cidr = '10.2.3.0/24'
        vpc1_fixture = self.useFixture(VPCFixture(connections=self.connections, cidr=cidr))

        assert vpc1_fixture.verify_on_setup(),"VPC verification failed, please check logs"

        return True
     # end test_create_delete_vpc

    @preposttest_wrapper
    def test_create_delete_vpc_false_cidr(self):
        """Create VPC failure with cidr with address mask not in range 16 to 28 """
        cidr1 = '10.2.3.0/29'
        cidr2 = '10.2.3.0/15'

        vpc_fixture = self.useFixture(VPCFixture( cidr1, connections = self.connections))
        assert not vpc_fixture.verify_on_setup(), \
            "VPC creation succeeded with invalid subnet of %s !" %(cird1)

        vpc1_fixture = self.useFixture(VPCFixture(cidr2, self.connections))
        assert not vpc1_fixture.verify_on_setup(), \
            "VPC creation succeeded with invalid subnet of %s!" % (cidr2)
        return True
    # end test_create_delete_vpc_false_cidr

    @preposttest_wrapper
    def test_subnet_create_delete(self):
        """Validate create subnet in vpc with valid CIDR """
        cidr = '10.2.3.0/24'
        vpc_fixture = self.useFixture(VPCFixture( cidr, connections = self.connections)) 
        vn_fixture = self.useFixture(VPCVNFixture(vpc_fixture,subnet_cidr=cidr, connections = self.connections))
        assert vn_fixture.verify_on_setup(),'Subnet verification failed'
        return True
    # end test_subnet_create_delete

    @preposttest_wrapper
    def test_subnet_create_delete_false_cidr(self):
        """Create subnet failure in vpc with invalid CIDR """
        cidr = '10.2.3.0/24'
        subnetCidr1 = '10.2.4.0/26'
        subnetCidr2 = '10.2.3.0/20'

        vpc_fixture = self.useFixture(VPCFixture( cidr, connections = self.connections))
        vn1_fixture = self.useFixture(VPCVNFixture(vpc_fixture,subnet_cidr=subnetCidr1,
                                      connections = self.connections))
        vn2_fixture = self.useFixture(VPCVNFixture(vpc_fixture,subnet_cidr=subnetCidr2, 
                                      connections = self.connections))
        assert not vn1_fixture.verify_on_setup(),'Subnet %s creation in VPC %s passed!' %( subnetCidr1,cidr)
        assert not vn2_fixture.verify_on_setup(),'Subnet %s creation in VPC %s passed!' %( subnetCidr2,cidr)

        return True
    # end test_subnet_create_delete_false_cidr

    @preposttest_wrapper
    def test_run_instance(self):
        """Launch a VM in subnet """
        cidr = '10.2.3.0/24'
        vpc_fixture = self.useFixture(VPCFixture( cidr, connections = self.connections))
        vpc_vn_fixture = self.useFixture(VPCVNFixture(vpc_fixture,subnet_cidr=cidr, connections = self.connections))
        vpc_vn_fixture.verify_on_setup()
        vm_fixture = self.useFixture(VPCVMFixture(
                            vpc_vn_fixture,
                            image_name='ubuntu',
                            connections=self.connections))
        vm_fixture.verify_on_setup()

        return True
    # end test_run_instance
    
    @preposttest_wrapper
    def test_ping_between_instances(self):
        """Test ping between instances in subnet """
        cidr1 = self.res.vpc1_cidr
        vpc1_fixture = self.res.vpc1_fixture
        vpc1_vn_fixture = self.res.vpc1_vn1_fixture
        vpc1_vn_fixture.verify_on_setup()
        assert vpc1_vn_fixture.verify_on_setup(),'Subnet verification failed'
        vm1_fixture = self.res.vpc1_vn1_vm1_fixture
        assert vm1_fixture.verify_on_setup(),"VPCVMFixture verification failed for VM %s" % (vm1_fixture.instance_id)
        vm2_fixture = self.res.vpc1_vn1_vm2_fixture
        assert vm2_fixture.verify_on_setup(),"VPCVMFixture verification failed for " \
                " VM %s" % (vm2_fixture.instance_id) 
        vm2_ip = vm2_fixture.c_vm_fixture.vm_ip
        assert vm1_fixture.c_vm_fixture.ping_with_certainty( vm2_ip, expectation=True ), "Ping " \
            "between two vms %s and %s failed!" % (vm1_fixture.instance_id, 
            vm2_fixture.instance_id)

        return True
    # end test_ping_between_instances

    @preposttest_wrapper
    def test_allocate_floating_ip(self):
        """Allocate a floating IP"""
        result = True
        cidr = '10.2.3.0/24'
        floatingIpCidr = '10.2.50.0/24'
        pool_name = 'pool1'
        
        # create public VN for floating ip pool

        vpc_fixture = self.res.vpc1_fixture
        assert vpc_fixture.verify_on_setup()," VPC %s verification failed" %( cidr)
        
        ec2_base = EC2Base(logger=self.inputs.logger, 
                           inputs=self.inputs,tenant='admin')
        fip_vn_fixture = self.useFixture(VNFixture(project_name='admin', 
                                            connections=self.connections, 
                                            inputs=self.inputs, 
                                            vn_name='public', 
                                            subnets=[floatingIpCidr]))
        assert fip_vn_fixture.verify_on_setup(),"FIP VN Fixture verification failed, Check logs"
        
        fip_vm_fixture= self.useFixture(VMFixture(
                                        project_name= 'admin', 
                                        connections= self.connections, 
                                        vn_obj= fip_vn_fixture.obj, 
                                        vm_name= 'fip_vm1'))
        assert fip_vm_fixture.verify_on_setup(),"VM verification in FIP VN failed"

        vm1_fixture = self.res.vpc1_vn1_vm1_fixture
        assert vm1_fixture.verify_on_setup(),"VPCVMFixture verification failed " \
                "for VM %s" % (vm1_fixture.instance_id) 
        
        fip_fixture = self.useFixture(VPCFIPFixture(
                                        fip_vn_fixture=fip_vn_fixture,
                                        connections=self.connections, 
                                        pool_name= pool_name,
                                        ec2_base=ec2_base))
        assert fip_fixture.verify_on_setup(),"FIP pool verification failed, Pls check logs"
        
        (fip, fip_alloc_id) = fip_fixture.create_and_assoc_fip(
                                            vm1_fixture.instance_id)
        if fip is None or fip_alloc_id is None:
            self.logger.error('FIP creation and/or association failed! ')
            result = result and False
        if result :
            self.addCleanup(fip_fixture.disassoc_and_delete_fip,
                            fip_alloc_id, fip)
            assert fip_fixture.verify_fip(fip)," FIP %s, %s verification failed" %(fip, fip_alloc_id)
            assert vm1_fixture.c_vm_fixture.ping_with_certainty(
                    fip_vm_fixture.vm_ip),"Ping from FIP IP failed"
            assert fip_vm_fixture.ping_with_certainty(fip),"Ping to FIP IP  failed"
        
        return result
    # end test_allocate_floating_ip

    @preposttest_wrapper
    def test_acl_with_association(self):
        """Create ACL, associate it with a subnet, add and replace rules """
        cidr = self.res.vpc1_vn1_cidr
        rule1 = {'number': '100', 'protocol': 'tcp', 'direction': 'egress', 'action': 'pass',
                'cidr': cidr, 'fromPort': '100', 'toPort': '200'}
        rule2 = {'number': '200', 'protocol': 'udp', 'direction': 'ingress', 'action': 'deny',
                'cidr': cidr, 'fromPort': '100', 'toPort': '200'}
        rule3 = {'number': '100', 'protocol': 'tcp', 'direction': 'egress', 'action': 'pass',
                'cidr': cidr, 'fromPort': '1000', 'toPort': '2000'}
        rule4 = {'number': '101', 'protocol': 'tcp', 'direction': 'egress', 'action': 'pass',
                'cidr': cidr, 'fromPort': '1000', 'toPort': '2000'}
        rule5 = {'number': '99', 'protocol': 'icmp', 'direction': 'egress', 'action': 'deny',
                'cidr': cidr,}
        rule6 = {'number': '98', 'protocol': 'icmp', 'direction': 'egress', 'action': 'pass',
                'cidr': cidr,}
        result = True
        
        vpc_fixture = self.res.vpc1_fixture
        vpc_vn_fixture = self.res.vpc1_vn1_fixture
        vm1_fixture = self.res.vpc1_vn1_vm1_fixture
        vm2_fixture = self.res.vpc1_vn1_vm2_fixture
        
        acl_id = self.createAcl(vpc_fixture)
        if not ( acl_id ):
            self.logger.error('ACL %s not seen ' % (acl_id))
            return False
        if not (vpc_vn_fixture.associate_acl(acl_id) and (vpc_vn_fixture.verify_acl_binding(acl_id))):
            self.logger.error('ACL %s association with Subnet %s failed' %( acl_id, vpc_vn_fixture.subnet_id) )
            result = result and False

        # create rule-1 and rule-2 in acl
        self.logger.info('Test create new rules')
        if not (self.createAclRule(vpc_fixture, acl_id, rule1) and self.createAclRule(vpc_fixture, acl_id, rule2)):
            self.logger.error('Creation of rules rule-1 and/or rule-2 failed')
            result = result and False

        self.logger.info('Test replace existing rules')
        # replace existing rule-1 with rule-3
        if not self.replaceAclRule(vpc_fixture, acl_id, rule3):
            self.logger.error('Replacing rule1 with rule3 failed')
            result = result and False

        self.logger.info('Test replace non-existing rules')
        # test replaceing not exixting rule-4
        if self.replaceAclRule(vpc_fixture, acl_id, rule4):
            self.logger.error('Replacing non-existant rule rule4 passed!')
            result = result and False

        self.logger.info('Test delete existing rules')
        # delete existing rule-3 and rule-2
        if not (self.deleteAclRule(vpc_fixture, acl_id, rule3) and self.deleteAclRule(vpc_fixture, acl_id, rule2)):
            self.logger.error('Deletion of rule2 and/or rule3 failed')
            result = result and False

        self.logger.info('Test delete non-existing rules')
        # test deleting non-exixting rule-4
        if self.deleteAclRule(vpc_fixture, acl_id, rule4):
            self.logger.error('Deletion of non-existant rule rule4 passed!')
            result = result and False
        
        #Test traffic now with deny on icmp and with allow on icmp
        self.createAclRule(vpc_fixture, acl_id, rule5)
        assert vm1_fixture.c_vm_fixture.ping_with_certainty(
                    vm2_fixture.c_vm_fixture.vm_ip,expectation=False), \
                    "With rule to deny ping, ping passed!"
        
        self.createAclRule(vpc_fixture, acl_id, rule6)
        assert vm1_fixture.c_vm_fixture.ping_with_certainty(
                    vm2_fixture.c_vm_fixture.vm_ip), \
                    "With rule to allow ping, ping failed!"

        if not (vpc_vn_fixture.associate_acl('acl-default') and vpc_vn_fixture.verify_acl_binding('acl-default')):
            self.logger.error('Unable to associate acl-default to subnet %s' %( vpc_vn_fixture.subnet_id))
            result = result and False
        
        #Cleanup 
        vpc_fixture.delete_acl(acl_id)

        return result
    # end test_acl_with_association

    @preposttest_wrapper
    def test_security_group(self):
        """Create Security Groups, Add and Delete Rules """
        result = True
        cidr = self.res.vpc1_cidr
        sg_name = 'sg1'
        rule1 = {'protocol': 'icmp', 'direction': 'egress',
                'cidr': cidr, }
        rule2 = {'protocol': 'tcp', 'direction': 'ingress',
                'cidr': cidr, 'port': '200-100'}
        rule3 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, }
        vpc_fixture = self.res.vpc1_fixture
        vpc_vn_fixture = self.res.vpc1_vn1_fixture

        # TODO
        # enable verify security group after
        # describe_security_groups has been fixed in nova cloud.py
        sg_id = self.createSecurityGroup(vpc_fixture, sg_name)
        if not (sg_id): # and self.verifySecurityGroup()):
            self.logger.error('Creation of SG %s failed' %(sg_name))
            result = result and False
        else:
            self.addCleanup(self.deleteSecurityGroup,vpc_fixture, sg_id)

        # create rule-1 and rule-2 in SG
        self.logger.info('Test create new rules')
        if not (self.createSgRule(vpc_fixture, sg_id, rule1) and self.createSgRule(vpc_fixture,sg_id,rule2)):
            self.logger.error('Unable to create rule1 and rule2 in SG %s ' %(sg_id))
            result = result and False

        # test create existing rule
        self.logger.info('Test create existing rule')
        if self.createSgRule(vpc_fixture,sg_id,rule1):
            self.logger.error('Able to create an existing rule in SG %s' %(sg_id))
            result = result and False
        else:
            self.logger.info('Unable to create an already existing rule rule1..OK')
        
        vm1_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu',
                                      connections=self.connections,
                                      sg_ids =[sg_name]))
        assert vm1_fixture.verify_on_setup(),"VPC1 VM fixture verification failed, check logs"
        vm1_fixture.c_vm_fixture.wait_till_vm_is_up() 
        vm2_fixture = self.res.vpc1_vn1_vm2_fixture
        # Without a rule for icmp, SG should drop ping packets
        if not vm2_fixture.c_vm_fixture.ping_with_certainty(
                    vm1_fixture.c_vm_fixture.vm_ip,expectation=False):
            self.logger.error("With no SG rule to allow ping, ping passed!")
            result = result and False
        
        self.createSgRule(vpc_fixture,sg_id,rule3) 
        time.sleep(5)
        # With a rule for icmp, SG should pass ping packets
        if not vm2_fixture.c_vm_fixture.ping_with_certainty( 
                    vm1_fixture.c_vm_fixture.vm_ip):
            self.logger.error("With SG rule to allow ping, ping failed!")
            result = result and False
        
        # test delete existing rules
        self.logger.info('Test delete existing rule')
        if not (self.deleteSgRule(vpc_fixture, sg_id, rule1) and self.deleteSgRule(vpc_fixture, sg_id,rule2)):
            self.logger.error('Unable to delete rules rule1 and rule2 in SG %s' %(sg_id))
            result = result and False
        else:
            self.logger.info('Deleted rules rule1 and rul2 in SG %s' %(sg_id))

        # test delete non-existing rule
        self.logger.info('Test delete non-existing rule')
        if self.deleteSgRule(vpc_fixture, sg_id, rule2):
            self.logger.error('Got success while deleting a non-existing rule rule2 in SG %s' %(sg_id))
            result = result and False
        else:
            self.logger.info('Unable to delete a non-existing rule rule2 in SG %s' %(sg_id))

        return result
    # end test_security_group
    
    @preposttest_wrapper
    def test_sg_tcp_udp(self):
        '''
        Validate TCP File transfer between VMs by creating rules in a SG
        '''
        result = True
        cidr = self.res.vpc1_cidr
        sg1_name = 'sg1'
        rule1 = {'protocol': 'tcp', 'direction': 'ingress',
                'cidr': cidr, 'port': '0-65535'}
        rule2 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, }
        rule3 = {'protocol': 'udp', 'direction': 'ingress',
                'cidr': cidr, 'port': '0-65535'}
        vpc_fixture = self.res.vpc1_fixture
        vpc_vn_fixture = self.res.vpc1_vn1_fixture
        vm2_fixture = self.res.vpc1_vn1_vm2_fixture

        sg1_id = self.createSecurityGroup(vpc_fixture, sg1_name)
        if not (sg1_id): 
            self.logger.error('Creation of SG %s failed' %(sg1_name))
            result = result and False
        else:
            self.addCleanup(vpc_fixture.delete_security_group,sg1_id)
        
        # create rule-1 and rule-2 in SG
        self.logger.info('Test create new rules')
        if not (self.createSgRule(vpc_fixture, sg1_id, rule1) and self.createSgRule(vpc_fixture, sg1_id, rule2)) :
            self.logger.error('Unable to create rule1/rule2 in SG %s ' %(sg1_id))
            result = result and False

        vm1_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu-tftp',
                                      connections=self.connections,
                                      sg_ids =[sg1_name]))
        assert vm1_fixture.verify_on_setup(),"VPC1 VM fixture verification failed, check logs"
        vm3_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu-tftp',
                                      connections=self.connections))
        assert vm3_fixture.verify_on_setup(),"VPC1 VM3 fixture verification failed, check logs"

        vm1_fixture.c_vm_fixture.wait_till_vm_is_up()
        vm3_fixture.c_vm_fixture.wait_till_vm_is_up()
        if not vm1_fixture.c_vm_fixture.ping_with_certainty(
                    vm2_fixture.c_vm_fixture.vm_ip):
            self.logger.error("With SG rule to allow ping, ping failed!")
            result = result and False
        transfer_result = vm3_fixture.c_vm_fixture.check_file_transfer(
                        dest_vm_fixture=vm1_fixture.c_vm_fixture,
                        mode='scp',
                        size=str(random.randint(100,1000000)))
        if not transfer_result:
            self.logger.error('File transfer step failed. Pls check logs')
            result = result and False
        
        # Validate tftp transfer fails without a rule
        transfer_result = vm1_fixture.c_vm_fixture.check_file_transfer(
                        dest_vm_fixture=vm3_fixture.c_vm_fixture,
                        mode='tftp',
                        size=str(random.randint(100,1000000)))
        if transfer_result:
            self.logger.error('File transfer step passed, expected it to fail. Pls check logs')
            result = result and False
       
        self.logger.info('Deleting the SG rule which allowed TCP and validate if transfer fails')
        self.deleteSgRule(vpc_fixture, sg1_id, rule1)
        transfer_result = vm3_fixture.c_vm_fixture.check_file_transfer(
                        dest_vm_fixture=vm1_fixture.c_vm_fixture,
                        mode='scp',
                        size=str(random.randint(100,1000000)))
        if transfer_result:
            self.logger.error('File transfer step passed which should have failed!!. Pls check logs')
            result = result and False
        
        self.logger.info('Adding an SG rule to allow UDP and validate that transfer passes')
        self.createSgRule(vpc_fixture, sg1_id, rule3)
        transfer_result = vm3_fixture.c_vm_fixture.check_file_transfer(
                        dest_vm_fixture=vm1_fixture.c_vm_fixture,
                        mode='tftp',
                        size=str(random.randint(100,1000000)))
        if not transfer_result:
            self.logger.error('File transfer step failed. Pls check logs')
            result = result and False
        
        return result
    # end test_sg_tcp_udp
    
    @preposttest_wrapper
    def test_sg_inside_group(self):
        '''
        Validate that SG rules to allow traffic within an SG
        
        Have VMs vm1,vm2,vm3 and SGs SG1, SG2. 
        SG1 to allow traffic from SG1 only (VM1)
        SG2 to allow traffic from SG1,SG3  (VM2)
        SG3 to allow traffic from SG3 only (VM3)
        VM1<->VM3 ping should fail
        VM2<->VM3 ping should pass 
        VM1<->VM2 ping should pass 
        '''
        result = True
        cidr = self.res.vpc1_cidr
        sg1_name = 'sg1'
        sg2_name = 'sg2'
        sg3_name = 'sg3'
        sg1_rule1 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, 'source-group': sg1_name,}
        sg2_rule1 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, 'source-group': sg1_name}
        sg2_rule2 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, 'source-group': sg3_name}
        sg3_rule1 = {'protocol': 'icmp', 'direction': 'ingress',
                'cidr': cidr, 'source-group': sg3_name}
        vpc_fixture = self.res.vpc1_fixture
        vpc_vn_fixture = self.res.vpc1_vn1_fixture

        sg1_id = self.createSecurityGroup(vpc_fixture, sg1_name)
        sg2_id = self.createSecurityGroup(vpc_fixture, sg2_name)
        sg3_id = self.createSecurityGroup(vpc_fixture, sg3_name)
        if not sg1_id or not sg2_id or not sg3_id:
            self.logger.error('Creation of SG %s/%s/%s failed' %(sg1_name,sg2_name, sg3_name))
            result = result and False
        else:
            self.addCleanup(vpc_fixture.delete_security_group,sg1_id)
            self.addCleanup(vpc_fixture.delete_security_group,sg2_id)
            self.addCleanup(vpc_fixture.delete_security_group,sg3_id)
        self.createSgRule(vpc_fixture, sg1_id, sg1_rule1)
        self.createSgRule(vpc_fixture, sg2_id, sg2_rule1)
        self.createSgRule(vpc_fixture, sg2_id, sg2_rule2)
        self.createSgRule(vpc_fixture, sg3_id, sg3_rule1)
        
        #Create VMs using the SGs
        vm1_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu',
                                      connections=self.connections,
                                      sg_ids =[sg1_name]))
        assert vm1_fixture.verify_on_setup(),"VPC VM1 fixture verification failed, check logs"
        vm2_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu',
                                      connections=self.connections,
                                      sg_ids =[sg2_name]))
        assert vm2_fixture.verify_on_setup(),"VPC VM2 fixture verification failed, check logs"
        vm3_fixture = self.useFixture(VPCVMFixture(vpc_vn_fixture,
                                      image_name='ubuntu',
                                      connections=self.connections,
                                      sg_ids =[sg3_name]))
        assert vm3_fixture.verify_on_setup(),"VPC1 VM3 fixture verification failed, check logs"
        vm1_fixture.c_vm_fixture.wait_till_vm_is_up()
        vm2_fixture.c_vm_fixture.wait_till_vm_is_up()
        vm3_fixture.c_vm_fixture.wait_till_vm_is_up()
        
        #Ping between VM1 and VM3 should fail
        if not vm1_fixture.c_vm_fixture.ping_with_certainty(
                    vm3_fixture.c_vm_fixture.vm_ip,expectation=False):
            self.logger.error('SG rule should have disallowed ping between Vm1,Vm3')
            result = result and False
        #ping between Vm3 and VM2 should pass
        if not vm3_fixture.c_vm_fixture.ping_with_certainty(
                    vm2_fixture.c_vm_fixture.vm_ip):
            self.logger.error("SG rule should have allowed ping between Vm2,Vm3")
            result = result and False
        
        #ping between Vm1 and VM2 should pass
        if not vm2_fixture.c_vm_fixture.ping_with_certainty(
                    vm1_fixture.c_vm_fixture.vm_ip):
            self.logger.error("SG rule should have allowed ping between Vm1,Vm2")
            result = result and False
        
        return result
    #end test_sg_inside_group
        
    
    @preposttest_wrapper
    def test_instance_stop_start(self):
        '''
        Validate stop and start of VM using EUCA cmds 
        '''
        vpc_fixture = self.res.vpc1_fixture
        vpc_vn_fixture = self.res.vpc1_vn1_fixture
        vm1_fixture = self.res.vpc1_vn1_vm1_fixture
        result = True
        
        if vm1_fixture.stop_instance():
            self.logger.error('Failed to stop instance!')
            result = result and False
        if vm1_fixture.verify_on_setup():
            self.logger.error('VM Fixture verification should have failed after stopping vm!')
            result = result and False
        if vm1_fixture.start_instance():
            self.logger.error('Failed to start instance!')
            result = result and False
        if not vm1_fixture.verify_on_setup():
            self.logger.error('VM Fixture verification failed after start vm')
            result = result and False
        return result 
    #end test_instance_stop_start
    
    @preposttest_wrapper
    def test_route_using_nat_instance(self):
        vpc1_fixture = self.res.vpc1_fixture
        vpc1_id = vpc1_fixture.vpc_id
        public_vn_subnet = self.inputs.fip_pool
        public_ip_to_ping = '8.8.8.8'
        public_vn_rt = self.inputs.mx_rt
        vpc1_vn1_fixture = self.res.vpc1_vn1_fixture
        vm1_fixture = self.res.vpc1_vn1_vm1_fixture
        result = True
       
        #Just Read the existing vpc as a fixture 
        vpc1_contrail_fixture = self.useFixture(
                                 ProjectFixture(
                                  vnc_lib_h= self.vnc_lib,
                                  project_name= vpc1_id,
                                  connections=self.connections))
        vpc1_contrail_fixture.get_project_connections()
        public_vn_fixture = self.useFixture(VNFixture(
                                 project_name=vpc1_id,
                                 connections=vpc1_contrail_fixture.project_connections,
                                 inputs=self.inputs,
                                 vn_name='public',
                                 subnets=[public_vn_subnet],
                                 rt_number=public_vn_rt))
        assert public_vn_fixture.verify_on_setup(),\
                "Public VN Fixture verification failed, Check logs"
        
        nat_instance_fixture = self.useFixture(VPCVMFixture(vpc1_vn1_fixture,
                                      image_name='nat-service',
                                      connections=vpc1_contrail_fixture.project_connections,
                                      instance_type='nat',
                                      public_vn_fixture=public_vn_fixture,
                                      ))
#        assert nat_instance_fixture.verify_on_setup(),\
#                "VPC NAT service instance fixture verification failed, check logs"
        
        # Create Route table
        rtb_id = vpc1_fixture.create_route_table()
        self.addCleanup(vpc1_fixture.delete_route_table,rtb_id)
        assert vpc1_fixture.verify_route_table(rtb_id),\
                "Verification of Routetable %s failed!" %(rtb_id)
        
        # Associate route table with subnet
        subnet_id = vpc1_vn1_fixture.subnet_id
        assoc_id = vpc1_fixture.associate_route_table(rtb_id, subnet_id)
        if not assoc_id:
            self.logger.error('Association of Subnet %s with RTB %s failed' \
                %(subnet_id, rtb_id))
            return False
        #end if 
        self.addCleanup(vpc1_fixture.disassociate_route_table, assoc_id)
        
        #Add route 
        prefix = '0.0.0.0/0'
        c_result = vpc1_fixture.create_route(prefix, 
                                            rtb_id,
                                            nat_instance_fixture.instance_id)
        if not c_result :
            self.logger.error('Unable to create default route in RTB %s with \
                instance %s ' %(rtb_id, vm1_fixture.instance_id))
            return False
        self.addCleanup(vpc1_fixture.delete_route,rtb_id,prefix)
        
        #Check if route is installed in agent
        c_vm1_fixture = vm1_fixture.c_vm_fixture
        vm1_node_ip = c_vm1_fixture.vm_node_ip
        agent_path = self.agent_inspect_h[vm1_node_ip].get_vna_active_route(
                 vrf_id= c_vm1_fixture.agent_vrf_id[ c_vm1_fixture.vn_fq_name ],
                 ip = prefix.split('/')[0],
                 prefix = prefix.split('/')[1])
        if not agent_path:
            self.logger.error('Route %s added is not seen in agent!' %
                                (prefix))
            result = result and False
        if not c_vm1_fixture.ping_with_certainty( 
                public_ip_to_ping, expectation=True ):
            self.logger.error('Ping to Public IP %s failed!' %(
            public_ip_to_ping))
            result = result and False
        return result
    #end test_route_using_nat_instance
        
if __name__ == '__main__':
    unittest.main()
