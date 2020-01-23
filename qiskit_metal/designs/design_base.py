# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing all Qiskit Metal designs.

@date: 2019
@author: Zlatko Minev, Thomas McConeky, ... (IBM)
"""
# To create a basic UML diagram
#>> pyreverse -o png -p desin_base design_base.py -A  -S

import numpy as np

from .. import Dict, draw, logger
from ..components.base import is_component
from ..config import DEFAULT, DEFAULT_OPTIONS
from ..toolbox_metal.import_export import load_metal, save_metal
from ..toolbox_metal.parsing import parse_params, parse_value

__all__ = ['DesignBase']

class DesignBase():
    """
    DesignBase is the base class for Qiskit Metal Designs.
    A design is the most top-level object in all of Qiskit Metal.
    """

    # TODO -- Break up DesignBase into several interface classes,
    # such as DesignConnectorInterface, DesignComponentInterface, etc.
    # in order to do a more Dependency Inversion Principle (DIP) style,
    # see also Dependency Injection (DI). This can also generalize nicely
    # to special flip chips, etc. to handle complexity!
    # Technically, components, connectors, variables, etc. are all separate entities
    # that can interface

    # Dummy private attribute used to check if an instanciated object is
    # indeed a DesignBase class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self):
        self._components = Dict()
        self._connectors = Dict()
        self._variables = Dict()
        self._chips = Dict()

        self._defaults = DEFAULT  # Depricated, to be removed
        self._default_options = DEFAULT_OPTIONS

        self.logger = logger

        # Notes, etc. that the user might want to store
        self.metadata = Dict(notes='')

#########PROPERTIES##################################################

    @property
    def components(self):
        '''
        Returns Dict object that keeps track of all Metal components in the design
        '''
        return self._components

    @property
    def connectors(self):
        '''
        Return the Dict object that keeps track of all connectors in the design.
        '''
        return self._connectors

    @property
    def variables(self):
        '''
        Return the Dict object that keeps track of all variables in the design.
        '''
        return self._variables

    @property
    def defaults(self):
        '''
        Return DEFAULT dictionary, which contains some key Metal DEFAULT params used
        in various Metal functions. These include default units, etc.

        Think of these as global defaults.
        '''
        return self._defaults

    @property
    def default_options(self):
        '''
        Return handle to the dicitonary of default options used in creating Metal
        component, and in calling other drawing and key functions.
        '''
        return self._default_options


#########Proxy properties##################################################


    def get_chip_size(self, chip_name='main'):
        raise NotImplementedError()

    def get_chip_z(self, chip_name='main'):
        raise NotImplementedError()

#########General methods###################################################

    def delete_all_connectors(self):
        '''
        Clear all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def delete_all_components(self):
        '''
        Clear all components in the design dictionary.
        Also clears all connectors.
        '''
        self._components.clear()
        self.delete_all_connectors()
        return self._components

    def make_all_components(self):
        """
        Remakes all components with their current parameters.
        """
        for name, obj in self.components.items():  # pylint: disable=unused-variable
            if is_component(obj):
                obj.make()

    def rename_component(self, component_name: str, new_component_name: str):
        """Rename component.

        Arguments:
            component_name {str} -- Old name
            new_component_name {str} -- New name

        Returns:
            int -- Results:
                1: True name is changed.
                -1: Failed, new component name exists.
                -2: Failed, invalid new name
        """
        #
        if new_component_name in self.components:
            self.logger.info(f'Cannot rename {component_name} to {new_component_name}. Since {new_component_name} exists')
            return -1

        # Check that the name is a valid component name
        if is_valid_component_name(component_name):
            self.logger.info(f'Cannot rename {component_name} to {new_component_name}.')
            return -2

        # do rename
            TODO
        return True

    def delete_component(self, component_name: str, force=False):
        """Deletes component and connectors attached to said component.
        If no component by that name is present, then just return True
        If component has dependencices return false and do not delete,
        unless force=True.

        Arguments:
            component_name {str} -- Name of component to delete

        Keyword Arguments:
            force {bool} -- force delete component even if it has children (default: {False})

        Returns:
            bool -- is there no such component
        """

        # Nothing to delete if name not in components
        if not component_name in self.components:
            self.logger.info('Called delete component {component_name}, but such a \
                             component is not in the design dicitonary of components.')
            return True

        # check if components has dependencies
        #   if it does, then do not delete, unless force=true
        #       logger.error('Cannot delete component{component_name}. It has dependencies. ')
        #          return false
        #   if it does not then delete

        # Do delete component ruthelessly
        return self._delete_component(component_name)

    def _delete_component(self, component_name: str):
        """Delete component without doing any checks.

        Returns:
            bool -- [description]
        """
        # Remove connectors
        connector_names = self.components[component_name].connector_names
        for c_name in connector_names:
            self.connectors.pop(c_name)

        # Remove from design dictionary of components
        self.components.pop(component_name, None)

        return True


#########I/O###############################################################

    @classmethod
    def load_design(cls, path):
        """Load a Metal design from a saved Metal file.
        (Class method)

        Arguments:
            path {str} -- Path to saved Metal design.

        Returns:
            Loaded metal design.
            Will also update default dicitonaries.
        """
        print("Beta feature. Not guaranteed to be fully implemented. ")
        return load_metal(path)

    def save_design(self, path):
        """Save the metal design to a Metal file.

        Arguments:
            path {str} -- Path to save the design to.
        """
        print("Beta feature. Not guaranteed to be fully implemented. ")
        return save_metal(self, path)

#########Creating Components###############################################################

    def parse_value(self, value):
        """
        Main parsing function.

        Parse a string, mappable (dict, Dict), iterrable (list, tuple) to account for
        units conversion, some basic arithmetic, and design variables.
        This is the main parsing function of Qiskit Metal.

        Handled Inputs:

            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmatic is possible, see below.
                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier `'variable1'.isidentifier()
                Strings of

            Dictionaries:
                Returns ordered `Dict` with same key-value mappings, where the values have
                been subjected to parse_value.

            Itterables(list, tuple, ...):
                Returns same kind and calls itself `parse_value` on each elemnt.

            Numbers:
                Returns the number as is. Int to int, etc.


        Arithemetic:
            Some basic arithemetic can be handled as well, such as `'-2 * 1e5 nm'`
            will yield float(-0.2) when the default units are set to `mm`.

        Default units:
            User units can be set in the design. The design will set config.DEFAULT.units

        Examples:
            See the docstring for this module.
                >> ?qiskit_metal.toolbox_metal.parsing

        Arguments:
            value {[str]} -- string to parse
            variable_dict {[dict]} -- dict pointer of variables

        Return:
            Parse value: str, float, list, tuple, or ast eval
        """
        return parse_value(value, self.variables)

    def parse_params(self, params: dict, param_names: str):
        """
        Extra utility function that can call parse_value on individual options.
        Use self.parse_value to parse only some options from a params dictionary

        Arguments:
            params (dict) -- Input dict to pull form
            param_names (str) -- eg, 'x,y,z,cpw_width'
        """
        return parse_params(params, param_names, variable_dict=self.variables)

    def add_connector(self, name: str, points: list, parent, flip=False, chip='main'):
        """Add named connector to the design by creating a connector dicitoanry.

        Arguments:
            name {str} -- Name of connector
            points {list} -- list of 2 2D points
            parent -- component or string or None. Will be converted to a string, which will
                      the name of the component.

        Keyword Arguments:
            points {list} --List of two points (default: {None})
            ops {dict} -- Optionally add options (default: {None})
        """
        if is_component(parent):
            parent = parent.name
        elif parent is None:
            parent = 'none'

        # assert isinstance(parent, str) # could enfornce
        self.connectors[name] = make_connector(
            points, parent, flip=flip, chip=chip)

    def update_component(self, component_name: str, dependencies=True):
        """Update the component and any dependencies it may have.
        Mediator type function to update all children.

        Arguments:
            component_name {str} -- [description]

        Keyword Arguments:
            dependencies {bool} -- Do update all dependencies (default: {True})
        """

        # Get dependency graph

        # Remake components in order
        pass


####################################################################################
###
# Connector
# TODO: Decide how to handle this.
#   Should this be a class?
#   Should we keep function here or just move into design?
# MAKE it so it has reference to who made it

def make_connector(points: list, parent_name, flip=False, chip='main'):
    """
    Works in user units.

    Arguments:
        points {[list of coordinates]} -- Two points that define the connector

    Keyword Arguments:
        flip {bool} -- Flip the normal or not  (default: {False})
        chip {str} -- Name of the chip the connector sits on (default: {'main'})

    Returns:
        [type] -- [description]
    """
    assert len(points) == 2

    # Get the direction vector, the unit direction vec, and the normal vector
    vec_dist, vec_dist_unit, vec_normal = draw.vec_unit_norm(points)

    if flip:
        vec_normal = -vec_normal

    return Dict(
        points=points,
        middle=np.sum(points, axis=0)/2.,
        normal=vec_normal,
        tangent=vec_dist_unit,
        width=np.linalg.norm(vec_dist),
        chip=chip,
        parent_name=parent_name
    )