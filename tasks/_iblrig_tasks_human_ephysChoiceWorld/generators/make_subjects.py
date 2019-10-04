from oneibl.one import ONE
one = ONE()
##
one.alyx.rest()  # get info on endpoints
one.alyx.rest('subjects')  # get info on subjects endpoint methods
one.alyx.rest('subjects', 'create')  # get info on create subjects

## now we have the dict structure:
for h in range(1, 201):
    nickname = 'human%04d'%h
    sub = {'nickname': nickname,
        'responsible_user': 'sfn_booth_user',
        'birth_date': '1900-01-01',
        'species': 'Human',
        'strain': 'Homo sapiens',
        'sex': 'U',
        'projects': ['sfn_booth_chicago2019'],
        'lab': 'churchlandlab'}
    print(sub)
    one.alyx.rest('subjects', 'create', data=sub)