# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2012 Nathan R. Yergler
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

from mysite.missions.base import Mission, MissionBaseView


class SetupIndex(MissionBaseView):
    url = '/'
    template_name = 'missions/windows-setup/about.html'
    view_name = 'main-page'
    title = 'What we recommend and why'


class SetupGitBash(MissionBaseView):
    url = '/install-git-bash'
    template_name = 'missions/windows-setup/install-git-bash.html'
    title = 'Install Git Bash'


class OpenGitBash(MissionBaseView):
    url = '/open-git-bash-prompt'
    template_name = 'missions/windows-setup/open-prompt.html'
    title = 'Open the Git Bash prompt'


class UnderstandingThePrompt(MissionBaseView):
    url = '/understand-prompt'
    template_name = 'missions/windows-setup/understand-prompt.html'
    title = 'Understanding the prompt and running programs'


class Navigating(MissionBaseView):
    url = '/navigating'
    template_name = 'missions/windows-setup/navigating.html'
    title = 'Navigating through folders'


class QuickReference(MissionBaseView):
    url = '/quick-reference'
    template_name = 'missions/windows-setup/quick-reference.html'
    title = 'Quick reference'


class Alternatives(MissionBaseView):
    url = '/alternatives'
    template_name = 'missions/windows-setup/alternatives.html'
    title = 'Alternatives'


class WindowsSetup(Mission):

    mission_id = 'windows-setup'
    name = 'Finding the command line on Windows'

    view_classes = (
        SetupIndex,
        SetupGitBash,
        OpenGitBash,
        UnderstandingThePrompt,
        Navigating,
        QuickReference,
        Alternatives,
    )
