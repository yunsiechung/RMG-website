#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#                                                                             #
# RMG Website - A Django-powered website for Reaction Mechanism Generator     #
#                                                                             #
# Copyright (c) 2011-2018 Prof. William H. Green (whgreen@mit.edu),           #
# Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)   #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the 'Software'),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

import re
import os
import urllib
import urllib2

import django.contrib.auth.views
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext, loader
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

from .forms import *

def index(request):
    """
    The RMG website homepage.
    """
    from rmgpy import __version__
    return render(request, 'index.html', {'version': __version__})

def privacy(request):
    """
    The RMG privacy policy.
    """
    return render(request, 'privacy.html', {'admins': settings.ADMINS})

def version(request):
    """
    Version information for RMG-website, RMG-Py, and RMG-database
    """
    return render(request, 'version.html')

def resources(request):
    """
    Page for accessing RMG resources, including papers and presentations
    """
    folder = os.path.join(settings.STATIC_ROOT, 'presentations')
    files = []

    if os.path.isdir(folder):
        files = os.listdir(folder)
        toRemove = []
        for f in files:
            if not os.path.isfile(os.path.join(folder, f)):
                # Remove any directories
                toRemove.append(f)
            elif f[0] == '.':
                # Remove any hidden files
                toRemove.append(f)
        for item in toRemove:
            files.remove(item)

    # Parse file names for information to display on webpage
    presentations = []
    if files:
        files.sort()
        for f in files:
            name = os.path.splitext(f)[0]
            parts = name.split('_')
            date = parts[0]
            date = date[0:4] + '-' + date[4:6] + '-' + date[6:]
            title = ' '.join(parts[1:])
            title = title.replace('+', ' and ')
            presentations.append((title, date, f))

    return render(request, 'resources.html', {'presentations': presentations})

def login(request):
    """
    Called when the user wishes to log in to his/her account.
    """
    return django.contrib.auth.views.login(request, template_name='login.html')

def logout(request):
    """
    Called when the user wishes to log out of his/her account.
    """
    return django.contrib.auth.views.logout(request, template_name='logout.html')

def signup(request):
    """
    Called when the user wishes to sign up for an account.
    """
    if request.method == 'POST':
        userForm = UserSignupForm(request.POST, error_class=DivErrorList)
        userForm.fields['first_name'].required = True
        userForm.fields['last_name'].required = True
        userForm.fields['email'].required = True
        profileForm = UserProfileSignupForm(request.POST, error_class=DivErrorList)
        passwordForm = PasswordCreateForm(request.POST, username='', error_class=DivErrorList)
        if userForm.is_valid() and profileForm.is_valid() and passwordForm.is_valid():
            username = userForm.cleaned_data['username']
            password = passwordForm.cleaned_data['password']
            userForm.save()
            passwordForm.username = username
            passwordForm.save()
            user = auth.authenticate(username=username, password=password)
            user_profile = UserProfile.objects.get_or_create(user=user)[0]
            profileForm2 = UserProfileSignupForm(request.POST, instance=user_profile, error_class=DivErrorList)
            profileForm2.save()
            auth.login(request, user)
            return HttpResponseRedirect('/')
    else:
        userForm = UserSignupForm(error_class=DivErrorList)
        profileForm = UserProfileSignupForm(error_class=DivErrorList)
        passwordForm = PasswordCreateForm(error_class=DivErrorList)
        
    return render(request, 'signup.html', {'userForm': userForm, 'profileForm': profileForm, 'passwordForm': passwordForm})

def viewProfile(request, username):
    """
    Called when the user wishes to view another user's profile. The other user
    is identified by his/her `username`. Note that viewing user profiles does
    not require authentication.
    """
    from rmgweb.pdep.models import Network
    user0 = User.objects.get(username=username)
    userProfile = user0.userprofile
    networks = Network.objects.filter(user=user0)
    return render(request, 'viewProfile.html', {'user0': user0, 'userProfile': userProfile, 'networks': networks})

@login_required
def editProfile(request):
    """
    Called when the user wishes to edit his/her user profile.
    """
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        userForm = UserForm(request.POST, instance=request.user, error_class=DivErrorList)
        profileForm = UserProfileForm(request.POST, instance=user_profile, error_class=DivErrorList)
        passwordForm = PasswordChangeForm(request.POST, username=request.user.username, error_class=DivErrorList)
        if userForm.is_valid() and profileForm.is_valid() and passwordForm.is_valid():
            userForm.save()
            profileForm.save()
            passwordForm.save()
            return HttpResponseRedirect(reverse('view-profile', kwargs={'username': request.user.username})) # Redirect after POST
    else:
        userForm = UserForm(instance=request.user, error_class=DivErrorList)
        profileForm = UserProfileForm(instance=user_profile, error_class=DivErrorList)
        passwordForm = PasswordChangeForm(error_class=DivErrorList)
        
    return render(request, 'editProfile.html', {'userForm': userForm, 'profileForm': profileForm, 'passwordForm': passwordForm})

def getAdjacencyList(request, identifier):
    """
    Returns an adjacency list of the species corresponding to `identifier`.
    
    `identifier` should be something recognized by NCI resolver, eg.
    SMILES, InChI, CACTVS, chemical name, etc.
    
    The NCI resolver has some bugs regarding reading SMILES of radicals.
    E.g. it thinks CC[CH] is CCC, so we first try to use the identifier
    directly as a SMILES string, and only pass it through the resolver
    if that does not work. 
    
    For specific problematic cases, the NCI resolver is bypassed and the SMILES
    is returned from a dictionary of values. For O2, the resolver returns the singlet
    form which is inert in RMG. For oxygen, the resolver returns 'O' as the SMILES, which
    is the SMILES for water.
    """
    from rmgpy.molecule import Molecule
    from rmgpy.exceptions import AtomTypeError
    from ssl import SSLError

    known_names = {
        'o2': '[O][O]',
        'oxygen': '[O][O]',
        'benzyl': '[CH2]c1ccccc1',
        'phenyl': '[c]1ccccc1',
    }

    # Ensure that input is a string
    identifier = str(identifier).strip()

    # Return empty string for empty input
    if identifier == '':
        return HttpResponse('', content_type="text/plain")

    molecule = Molecule()

    # Check if identifier is an InChI string
    if identifier.startswith('InChI=1'):
        try:
            molecule.fromInChI(identifier)
        except AtomTypeError:
            return HttpResponse('Invalid Molecule', status=501)
        except KeyError, e:
            return HttpResponse('Invalid Element: {0!s}'.format(e), status=501)
    elif identifier.lower() in known_names:
        molecule.fromSMILES(known_names[identifier.lower()])
    else:
        try:
            # Try parsing as a SMILES string
            molecule.fromSMILES(identifier)
        except AtomTypeError:
            return HttpResponse('Invalid Molecule', status=501)
        except KeyError, e:
            return HttpResponse('Invalid Element: {0!s}'.format(e), status=501)
        except (IOError, ValueError):
            # Try converting it to a SMILES using the NCI chemical resolver
            url = "https://cactus.nci.nih.gov/chemical/structure/{0}/smiles".format(urllib.quote(identifier))
            try:
                f = urllib2.urlopen(url, timeout=5)
            except urllib2.URLError, e:
                return HttpResponse("Could not identify {0}. NCI resolver responded with {1}.".format(identifier, e), status=404)
            except SSLError:
                return HttpResponse('NCI resolver timed out, please try again.', status=504)
            smiles = f.read()
            try:
                molecule.fromSMILES(smiles)
            except AtomTypeError:
                return HttpResponse('Invalid Molecule', status=501)
            except KeyError, e:
                return HttpResponse('Invalid Element: {0!s}'.format(e), status=501)
            except ValueError, e:
                return HttpResponse(str(e), status=500)
    
    adjlist = molecule.toAdjacencyList(removeH=False)
    return HttpResponse(adjlist, content_type="text/plain")

def getNISTcas(request, inchi):
    """
    Get the CAS number as used by NIST, from an InChI
    """
    url = "http://webbook.nist.gov/cgi/inchi/{0}".format(urllib.quote(inchi))
    try:
        f = urllib2.urlopen(url, timeout=5)
    except urllib2.URLError, e:
        return HttpResponseNotFound("404: Couldn't identify {0}. NIST responded {1} to request for {2}".format(inchi, e, url))
    searcher = re.compile('<li><a href="/cgi/inchi\?GetInChI=C(\d+)')
    for line in f:
        m = searcher.match(line)
        if m:
            number = m.group(1)
            break
    else:
        return HttpResponseNotFound("404: Couldn't identify {0}. Couldn't locate CAS number in page at {1}".format(inchi, url))
    return HttpResponse(number, content_type="text/plain")
    
def cactusResolver(request, query):
    """
    Forwards the query to the cactus.nci.nih.gov/chemical/structure resolver.
    
    The reason we have to forward the request from our own server is so that we can 
    use it via ajax, avoiding cross-domain scripting security constraints.
    """
    from ssl import SSLError

    if query.strip() == '':
        return HttpResponse('', content_type="text/plain")
   
    url = "https://cactus.nci.nih.gov/chemical/structure/{0}".format(urllib.quote(query))
    try:
        f = urllib2.urlopen(url, timeout=5)
    except urllib2.URLError, e:
        return HttpResponse("Could not process request. NCI resolver responded with {0}.".format(e), status=404)
    except SSLError:
        return HttpResponse('NCI resolver timed out, please try again.', status=504)
    response = f.read()
    return HttpResponse(response, content_type="text/plain")
    
def drawMolecule(request, adjlist, format='png'):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecule.
    urllib is used to quote/unquote the adjacency list.
    """
    from rmgpy.molecule import Molecule
    from rmgpy.molecule.draw import MoleculeDrawer
    from rmgpy.molecule.adjlist import InvalidAdjacencyListError

    adjlist = str(urllib.unquote(adjlist))

    try:
        molecule = Molecule().fromAdjacencyList(adjlist)
    except (InvalidAdjacencyListError, ValueError):
        response = HttpResponseRedirect(static('img/invalid_icon.png'))
    else:
        if format == 'png':
            response = HttpResponse(content_type="image/png")
            surface, _, _ = MoleculeDrawer().draw(molecule, format='png')
            surface.write_to_png(response)
        elif format == 'svg':
            response = HttpResponse(content_type="image/svg+xml")
            MoleculeDrawer().draw(molecule, format='svg', target=response)
        else:
            response = HttpResponse('Image format not implemented.', status=501)

    return response

def drawGroup(request, adjlist, format='png'):
    """
    Returns an image of the provided adjacency list `adjlist` for a molecular
    group.  urllib is used to quote/unquote the adjacency list.
    """
    from rmgpy.molecule.group import Group
    from rmgpy.molecule.adjlist import InvalidAdjacencyListError

    adjlist = str(urllib.unquote(adjlist))

    try:
        group = Group().fromAdjacencyList(adjlist)
    except (InvalidAdjacencyListError, ValueError):
        response = HttpResponseRedirect(static('img/invalid_icon.png'))
    else:
        if format == 'png':
            response = HttpResponse(content_type="image/png")
            response.write(group.draw('png'))
        elif format == 'svg':
            response = HttpResponse(content_type="image/svg+xml")
            svgdata = group.draw('svg')
            # Remove the scale and rotate transformations applied by pydot
            svgdata = re.sub(r'scale\(0\.722222 0\.722222\) rotate\(0\) ', '', svgdata)
            response.write(svgdata)
        else:
            response = HttpResponse('Image format not implemented.', status=501)

    return response

@login_required
def restartWSGI(request):
    if request.META['mod_wsgi.process_group'] != '':
        import signal, os, sys
        restart_filename = os.path.join(os.path.dirname(request.META['SCRIPT_FILENAME']), 'restart')
        print >> sys.stderr, "Touching {0} to trigger a restart all daemon processes".format(restart_filename)
        with file(restart_filename, 'a'):
            os.utime(restart_filename, None)
        #os.kill(os.getpid(), signal.SIGINT)
    return HttpResponseRedirect('/')

def debug(request):
    import sys
    import scipy, numpy
    print >> sys.stderr, "scipy module is {0}".format(scipy)
    print >> sys.stderr, "numpy.finfo(float) = {0}".format(numpy.finfo(float))
    print >> sys.stderr, "Failing on purpose to trigger a debug screen"
    assert False, "Intentional failure to trigger debug screen."

@csrf_exempt
def rebuild(request):
    import os
    rebuild_filename = os.path.join(os.path.dirname(request.META['DOCUMENT_ROOT']), 'trigger/rebuild')
    with file(rebuild_filename, 'a'):
            os.utime(rebuild_filename, None)
    return HttpResponseRedirect('/')

def custom500(request):
    import sys, traceback
    template = loader.get_template('500.html')
    etype, value = sys.exc_info()[:2]
    exception = ''.join(traceback.format_exception_only(etype, value)).strip()
    return HttpResponseServerError(template.render(context={'exception': exception}))
