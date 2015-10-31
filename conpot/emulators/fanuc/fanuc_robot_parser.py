import re

RE_ROBOT_POSITION_START = re.compile("CURRENT\s+ROBOT\s+POSITION")
RE_ROBOT_POSITION_GROUP = re.compile("Group\s+\#\:\s+(?P<NO>\d+)")

RE_ROBOT_JOINT_POSITION_START = re.compile("CURRENT\s+JOINT\s+POSITION")
RE_ROBOT_JOINT_POSITION_GROUP = re.compile("Joint\s+(?P<NO>\d+)\:\s+(?P<VALUE>[-+]?\d*\.?\d+)")
RE_ROBOT_JOINT_EXTAXS_POSITION_GROUP = re.compile("EXTAXS\:\s+(?P<NO>\d+)\:\s+(?P<VALUE>[-+]?\d*\.?\d+)")

class RobotoPositionParser:
    def __init__(self):
        pass

    def parse(self, lines):
        def read_until_reg_found(reg, current_pos, lines):
            m = None
            for i, line in enumerate(lines[current_pos:]):
                m = reg.match(line)
                if m:
                    current_pos = current_pos + i + 1
                    break
            return (current_pos, m)

        answer = {1:[], 2:[], 3:[]}

        current_pos = 0
        ################## GROUP 1 ##################
        # PARSE ROBOT POSITION
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT ROBOT POSITION'"

        # PARSE ROBOT GROUP
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Group #: <>'"
        print "GROUP: ", m.group("NO")

        # JOINT POSITION START
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT JOINT POSITION'"

        # GROUP 1 JOINT 1
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1] = [eval(m.group("VALUE"))]

        # GROUP 1 JOINT 2
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        # GROUP 1 JOINT 3
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        # GROUP 1 JOINT 4
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        # GROUP 1 JOINT 5
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        # GROUP 1 JOINT 6
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        # GROUP 1 JOINT EXTAXS
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_EXTAXS_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'EXTAXS   <>:      <>'"
        print "EXTAXS ", m.group("NO"), ": ", m.group("VALUE")
        answer[1].append(eval(m.group("VALUE")))

        ################## GROUP 2 ##################
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT ROBOT POSITION'"

        # PARSE ROBOT GROUP
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Group #: <>'"
        print "GROUP: ", m.group("NO")

        # JOINT POSITION START
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT JOINT POSITION'"

        # GROUP 2 JOINT 1
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[2].append(eval(m.group("VALUE")))

        # GROUP 2 JOINT 2
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[2].append(eval(m.group("VALUE")))

        ################## GROUP 3 ##################
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT ROBOT POSITION'"

        # PARSE ROBOT GROUP
        current_pos, m = read_until_reg_found(RE_ROBOT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Group #: <>'"
        print "GROUP: ", m.group("NO")

        # JOINT POSITION START
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_START, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'CURRENT JOINT POSITION'"

        # GROUP 3 JOINT 1
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[3].append(eval(m.group("VALUE")))

        # GROUP 3 JOINT 2
        current_pos, m = read_until_reg_found(RE_ROBOT_JOINT_POSITION_GROUP, current_pos, lines)
        if not m:
            #TODO: ERROR
            raise "Can Not found 'Joint   <>:      <>'"
        print "Joint ", m.group("NO"), ": ", m.group("VALUE")
        answer[3].append(eval(m.group("VALUE")))

        return answer