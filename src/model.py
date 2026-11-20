#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   model.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: haranivo <haranivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/11/20 07:34:51 by haranivo            #+#    #+#            #
#   Updated: 2026/11/20 08:00:03 by haranivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Regrouping blueprints object models."""


from dataclasses import dataclass
from pydantic import BaseModel, Field, model_validator


class Prompt(BaseModel):
    """Verify, validate and create prompt object."""

    prompt: dict = Field(default_factory=dict)
