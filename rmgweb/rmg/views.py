#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#	RMG Website - A Django-powered website for Reaction Mechanism Generator
#
#	Copyright (c) 2011 Prof. William H. Green (whgreen@mit.edu) and the
#	RMG Team (rmg_dev@mit.edu)
#
#	Permission is hereby granted, free of charge, to any person obtaining a
#	copy of this software and associated documentation files (the 'Software'),
#	to deal in the Software without restriction, including without limitation
#	the rights to use, copy, modify, merge, publish, distribute, sublicense,
#	and/or sell copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#	DEALINGS IN THE SOFTWARE.
#
################################################################################

import os.path
import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from rmgweb.rmg.models import *
from rmgweb.rmg.forms import *

from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.group import Group
from rmgpy.thermo import *
from rmgpy.kinetics import *

from rmgpy.data.base import Entry
from rmgpy.data.thermo import ThermoDatabase
from rmgpy.data.kinetics import *
from rmgpy.data.rmg import RMGDatabase

from rmgweb.main.tools import *
from rmgweb.database.views import loadDatabase

################################################################################


def index(request):
    """
    The RMG simulation homepage.
    """
    return render_to_response('rmg.html', context_instance=RequestContext(request))

def convertChemkin(request):
    """
    Allows user to upload chemkin and RMG dictionary files to generate a nice looking html output.
    """
    chemkin = Chemkin()
    chemkin.setReqObj(request)
    path = ''
    chemkin.deleteDir()

    if request.method == 'POST':
        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)
        if form.is_valid():
            form.save()
            timestr = str(chemkin.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = chemkin.getUsername()
            form.cleaned_data['name'] = userid
            path = 'media/'+userid+'/rmg/tools/chemkin/'+timestr+'/output.html'
            # Generate the output HTML file
            chemkin.createOutput()
            # Go back to the network's main page
            return render_to_response('chemkinUpload.html', {'form': form, 'path':path}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = UploadChemkinForm(instance=chemkin)

    return render_to_response('chemkinUpload.html', {'form': form,'path':path}, context_instance=RequestContext(request))

def convertAdjlists(request):
    """
    Allows user to upload a dictionary txt file and convert it back into old style adjacency lists in the form of a txt file.
    """
    conversion = AdjlistConversion()
    conversion.setReqObj(request)
    path = ''
    conversion.deleteDir()

    if request.method == 'POST':
        form = UploadDictionaryForm(request.POST, request.FILES, instance=conversion)
        if form.is_valid():
            form.save()
            timestr = str(conversion.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = conversion.getUsername()
            path = 'media/'+userid+'/rmg/tools/adjlistConversion/'+timestr+'/RMG_Dictionary.txt'
            # Generate the output HTML file
            conversion.createOutput()
            # Go back to the network's main page
            return render_to_response('dictionaryUpload.html', {'form': form, 'path':path}, context_instance=RequestContext(request))

    # Otherwise create the form
    else:
        form = UploadDictionaryForm(instance=conversion)

    return render_to_response('dictionaryUpload.html', {'form': form,'path':path}, context_instance=RequestContext(request))

def compareModels(request):
    """
    Allows user to compare 2 RMG models with their chemkin and species dictionaries and generate
    a pretty HTML diff file.
    """
    diff = Diff()
    diff.setReqObj(request)
    path = ''
    diff.deleteDir()

    if request.method == 'POST':
        form = ModelCompareForm(request.POST, request.FILES, instance=diff)
        if form.is_valid():
            form.save()
            timestr = str(diff.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = diff.getUsername()
            path = 'media/'+userid+'/rmg/tools/compare/'+timestr+'/diff.html'
            # Generate the output HTML file
            diff.createOutput()
            return render_to_response('modelCompare.html', {'form': form, 'path':path}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = ModelCompareForm(instance=diff)

    return render_to_response('modelCompare.html', {'form': form,'path':path}, context_instance=RequestContext(request))


def mergeModels(request):
    """
    Merge 2 RMG models with their chemkin and species dictionaries.
    Produces a merged chemkin file and species dictionary.
    """
    model = Diff()
    model.setReqObj(request)
    path = ''
    model.deleteDir()

    if request.method == 'POST':
        form = ModelCompareForm(request.POST, request.FILES, instance = model)
        if form.is_valid():
            form.save()
            model.merge()
            timestr = str(model.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = model.getUsername()
            path = 'media/'+userid+'/rmg/tools/compare/'+timestr
            #[os.path.join(model.path,'chem.inp'), os.path.join(model.path,'species_dictionary.txt'), os.path.join(model.path,'merging_log.txt')]
            return render_to_response('mergeModels.html', {'form': form, 'path':path}, context_instance=RequestContext(request))
    else:
        form = ModelCompareForm(instance=model)

    return render_to_response('mergeModels.html', {'form': form,'path':path}, context_instance=RequestContext(request))



def generateFlux(request):
    """
    Allows user to upload a set of RMG condition files and/or chemkin species concentraiton output
    to generate a flux diagram video.
    """

    flux = FluxDiagram()
    flux.setReqObj(request)
    subdirs = []
    flux.deleteDir()

    if request.method == 'POST':
        form = FluxDiagramForm(request.POST, request.FILES,instance=flux)
        if form.is_valid():
            form.save()
            flux.createOutput(form)
            timestr = str(flux.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = flux.getUsername()
            path = flux.getPath()
            prefix = 'media/'+userid+'/rmg/tools/flux/'+timestr
            # Look at number of subdirectories to determine where the flux diagram videos are
            subdirs = [prefix+'/'+name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
            subdirs.remove(prefix+'/species')
            return render_to_response('fluxDiagram.html', {'form': form, 'path':subdirs}, context_instance=RequestContext(request))

    else:
        form = FluxDiagramForm(instance=flux)

    return render_to_response('fluxDiagram.html', {'form': form,'path':subdirs}, context_instance=RequestContext(request))


def runPopulateReactions(request):
    """
    Allows user to upload chemkin and RMG dictionary files to generate a nice looking html output.
    """
    populateReactions = PopulateReactions()
    populateReactions.setReqObj(request)
    outputPath = ''
    chemkinPath = ''
    populateReactions.deleteDir()

    if request.method == 'POST':
        form = PopulateReactionsForm(request.POST, request.FILES, instance=populateReactions)
        if form.is_valid():
            form.save()
            timestr = str(populateReactions.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            userid = populateReactions.getUsername()
            outputPath = 'media/'+userid+'/rmg/tools/populateReactions/'+timestr+'/output.html'
            chemkinPath = 'media/'+userid+'/rmg/tools/populateReactions/chemkin/'+timestr+'/chem.inp'
            # Generate the output HTML file
            populateReactions.createOutput()
            # Go back to the network's main page
            return render_to_response('populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath}, context_instance=RequestContext(request))


    # Otherwise create the form
    else:
        form = PopulateReactionsForm(instance=populateReactions)

    return render_to_response('populateReactionsUpload.html', {'form': form, 'output': outputPath, 'chemkin': chemkinPath}, context_instance=RequestContext(request))



def input(request):
    ThermoLibraryFormset = inlineformset_factory(Input, ThermoLibrary, ThermoLibraryForm,
                                                 BaseInlineFormSet, extra=1, can_delete=True)
    ReactionLibraryFormset = inlineformset_factory(Input, ReactionLibrary, ReactionLibraryForm,
                                                   BaseInlineFormSet, extra=1, can_delete=True)
    ReactorSpeciesFormset = inlineformset_factory(Input, ReactorSpecies, ReactorSpeciesForm,
                                                  BaseInlineFormSet, extra = 1, can_delete=True)
    ReactorFormset = inlineformset_factory(Input, Reactor, ReactorForm,
                                           BaseInlineFormSet, extra = 1, can_delete=True)

    Input.objects.all().delete()
    input = Input()
    input.deleteDir()

    uploadform = UploadInputForm(instance=input)
    form = InputForm(instance=input)
    thermolibformset = ThermoLibraryFormset(instance=input)
    reactionlibformset = ReactionLibraryFormset(instance=input)
    reactorspecformset = ReactorSpeciesFormset(instance=input)
    reactorformset = ReactorFormset(instance=input)
    upload_error = ''
    input_error = ''

    if request.method == 'POST':
        input.createDir()

        # Load an input file into the form by uploading it
        if "upload" in request.POST:
            uploadform = UploadInputForm(request.POST, request.FILES, instance=input)
            if uploadform.is_valid():
                uploadform.save()
                initial_thermo_libraries, initial_reaction_libraries, initial_reactor_systems, initial_species, initial = input.loadForm(input.loadpath)

                # Make the formsets the lengths of the initial data
                if initial_thermo_libraries:
                    ThermoLibraryFormset = inlineformset_factory(Input, ThermoLibrary, ThermoLibraryForm, BaseInlineFormSet,
                                                                 extra=len(initial_thermo_libraries), can_delete=True)
                if initial_reaction_libraries:
                    ReactionLibraryFormset = inlineformset_factory(Input, ReactionLibrary, ReactionLibraryForm, BaseInlineFormSet,
                                                               extra=len(initial_reaction_libraries), can_delete=True)
                ReactorSpeciesFormset = inlineformset_factory(Input, ReactorSpecies, ReactorSpeciesForm, BaseInlineFormSet,
                                                              extra=len(initial_species), can_delete=True)
                ReactorFormset = inlineformset_factory(Input, Reactor, ReactorForm, BaseInlineFormSet,
                                                       extra = len(initial_reactor_systems), can_delete=True)
                thermolibformset = ThermoLibraryFormset()
                reactionlibformset = ReactionLibraryFormset()
                reactorspecformset = ReactorSpeciesFormset()
                reactorformset = ReactorFormset()

                # Load the initial data into the forms
                form = InputForm(initial = initial)
                for subform, data in zip(thermolibformset.forms, initial_thermo_libraries):
                    subform.initial = data
                for subform, data in zip(reactionlibformset.forms, initial_reaction_libraries):
                    subform.initial = data
                for subform, data in zip(reactorspecformset.forms, initial_species):
                    subform.initial = data
                for subform, data in zip(reactorformset.forms, initial_reactor_systems):
                    subform.initial = data

            else:
                upload_error = 'Your input file was invalid.  Please try again.'

        if "submit" in request.POST:
            uploadform = UploadInputForm(request.POST, instance=input)
            form = InputForm(request.POST, instance = input)
            thermolibformset = ThermoLibraryFormset(request.POST, instance=input)
            reactionlibformset = ReactionLibraryFormset(request.POST, instance=input)
            reactorspecformset = ReactorSpeciesFormset(request.POST, instance=input)
            reactorformset = ReactorFormset(request.POST, instance=input)

            if (form.is_valid() and thermolibformset.is_valid() and reactionlibformset.is_valid()
                and reactorspecformset.is_valid() and reactorformset.is_valid()):
                form.save()
                thermolibformset.save()
                reactionlibformset.save()
                reactorspecformset.save()
                reactorformset.save()
                posted = Input.objects.all()[0]
                input.saveForm(posted, form)
                path = 'media/rmg/tools/input/input.py'
                return render_to_response('inputResult.html', {'path': path})

            else:
                # Will need more useful error messages later.
                input_error = 'Your form was invalid.  Please edit the form and try again.'

    return render_to_response('input.html', {'uploadform': uploadform, 'form': form, 'thermolibformset':thermolibformset,
                                             'reactionlibformset':reactionlibformset, 'reactorspecformset':reactorspecformset,
                                             'reactorformset':reactorformset, 'upload_error': upload_error,
                                             'input_error': input_error}, context_instance=RequestContext(request))



def plotKinetics(request):
    """
    Allows user to upload chemkin files to generate a plot of reaction kinetics.
    """
    from rmgpy.quantity import Quantity
    from rmgweb.database.forms import RateEvaluationForm


    if request.method == 'POST':
        chemkin = Chemkin()
        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)
        chemkin.setReqObj(request)
        rateForm = RateEvaluationForm(request.POST)
        eval = []


        if rateForm.is_valid():
            temperature = Quantity(rateForm.cleaned_data['temperature'], str(rateForm.cleaned_data['temperature_units'])).value_si
            pressure = Quantity(rateForm.cleaned_data['pressure'], str(rateForm.cleaned_data['pressure_units'])).value_si
            eval = [temperature, pressure]
            kineticsDataList = chemkin.getKinetics()

        if form.is_valid():
            form.save()
            kineticsDataList = chemkin.getKinetics()



        return render_to_response('plotKineticsData.html', {'kineticsDataList': kineticsDataList,
                                                'plotWidth': 500,
                                                'plotHeight': 400 + 15 * len(kineticsDataList),
                                                'form': rateForm,
                                                'eval':eval },
                                         context_instance=RequestContext(request))

    # Otherwise create the form
    else:


        chemkin = Chemkin()
        chemkin.setReqObj(request)
        chemkin.deleteDir()
        form = UploadChemkinForm(instance=chemkin)

    return render_to_response('plotKinetics.html', {'form': form}, context_instance=RequestContext(request))


def javaKineticsLibrary(request):
    """
    Allows user to upload chemkin files to generate a plot of reaction kinetics.
    """
    from rmgpy.quantity import Quantity

    if request.method == 'POST':
        chemkin = Chemkin()
        chemkin.setReqObj(request)
        path = ''

        form = UploadChemkinForm(request.POST, request.FILES, instance=chemkin)
        if form.is_valid():
            form.save()
            chemkin.createJavaKineticsLibrary()
            userid = chemkin.getUsername()
            timestr = str(chemkin.getTime())
            timestr = timestr.replace(':','.')[:len(timestr)-7]
            path = 'media/'+userid+'/rmg/tools/chemkin/'+timestr
        return render_to_response('javaKineticsLibrary.html', {'form': form,
                                                'path': path },
                                         context_instance=RequestContext(request))

    # Otherwise create the form
    else:


        chemkin = Chemkin()
        chemkin.setReqObj(request)
        chemkin.deleteDir()
        form = UploadChemkinForm(instance=chemkin)

    return render_to_response('javaKineticsLibrary.html', {'form': form}, context_instance=RequestContext(request))


def evaluateNASA(request):
    """
    Creates webpage form form entering a chemkin format NASA Polynomial and quickly
    obtaining it's enthalpy and Cp values.
    """
    from rmgpy.chemkin import readThermoEntry
    form = NASAForm()
    thermo = None
    thermoData = None
    if request.method == 'POST':
        posted = NASAForm(request.POST, error_class=DivErrorList)
        initial = request.POST.copy()

        if posted.is_valid():
                NASA = posted.cleaned_data['NASA']
                if NASA != '':
                    species, thermo, formula = readThermoEntry(str(NASA))
                    try:
                        thermoData = thermo.toThermoData()
                    except:
                        # if we cannot convert the thermo to thermo data, we will not be able to display the
                        # H298, S298, and Cp values, but that's ok.
                        pass

        form = NASAForm(initial, error_class=DivErrorList)

    return render_to_response('NASA.html', {'form': form, 'thermo':thermo, 'thermoData':thermoData}, context_instance=RequestContext(request))
