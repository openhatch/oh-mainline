# This file is part of OpenHatch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class IncorrectPipOutput(Exception):
    pass


def validate_pip_freeze_output(output):

    if 'requests' not in output:
        raise IncorrectPipOutput, 'Looks like you do not have Requests installed. Make \
        sure that you followed the instructions above and also make sure that you did not miss \
        anything while copying the output of the pip freeze command from the terminal.'


def validate_pip_list_output(output):

    if 'requests' in output:
        raise IncorrectPipOutput, "According to the output of the pip list command that you \
        submitted, Requests is still installed in your virtualenv. One possible reason for this \
        is that you ran pip list before uninstalling Requests; if so, uninstall Requests by \
        following the instructions above and then run pip list and copy it's output and submit it again." 
