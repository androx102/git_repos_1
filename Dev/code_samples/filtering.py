

dummy_text = "[22.678] 1:8; sys_man_ps.c:811; NOTIFY - SysM- PS data set Always_On: 1"
substring = "data set Always_On: 1"

if substring in dummy_text:
    print("True")
else:
    print("Not found")