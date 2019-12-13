from django.shortcuts import render


def results(request):
    context = {'results_header': "Your Search was interpeted as: F(x) = m * a",
               'terms_list': ['term1'],
               'result_dict': {"Newton's laws of motion": ["Second law:	In an inertial frame of reference, "
                                                           "the vector sum of the forces F on an object is equal to ",
                                                           "the mass m of that object multiplied by the acceleration"
                                                           "a of the object: <b>F = ma</b>. (It is assumed here that",
                                                           "the mass m is constant – see below.)"],
                               "Kinematics": ["The acceleration of a particle is the vector defined by the rate of"
                                              " change of the velocity vector.",
                                              " The average acceleration of a particle "
                                              "over a time interval is defined as the ratio."]},

               'term_string': 'fx=ma',
               'facets': [('Maths', 'Maths', ''),
                          ('Physics', 'Physics', ''),
                          ('Biology', 'Biology', ''),
                          ('Economics', 'Economics', '')],
               'related': [('Kinematics', 1),
                           ('Classical Mechanics', 1),
                           ('Issac Newton', 1)],
               }
    return render(request, 'home/results.html', context)


def home(request):
    context = {}
    return render(request, 'home/home.html', context)
