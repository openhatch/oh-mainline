(function ($) {
    "use strict";
    var attr_old = $.fn.attr;
    $.fn.attr = function () {
        var a, aLength, attributes,  map;
        if (this[0] && arguments.length === 0) {
            map = {};
            attributes = this[0].attributes;
            aLength = attributes.length;
            for (a = 0; a < aLength; a = a + 1) {
                map[attributes[a].name.toLowerCase()] = attributes[a].value;
            }
            return map;
        }
        return attr_old.apply(this, arguments);
    };
    $.fn.redraw = function () {
        return this.hide(0, function () {
            $(this).show();
        });
    };
    $.fn.invisible = function () {
        return this.each(function () {
            $(this).css("visibility", "hidden");
        });
    };
    $.fn.visible = function () {
        return this.each(function () {
            $(this).css("visibility", "visible");
        });
    };
    $.fn.inplaceeditform = function (method) {
        var methods = $.inplaceeditform.methods;

        // method calling logic
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        }
        if (typeof method === "object" || !method) {
            return methods.init.apply(this, arguments);
        }
        $.error("Method " + method + " does not exist on jQuery.inplaceeditform");
    };
    $.inplaceeditform = {
        opts: {
            "getFieldUrl": "/inplaceeditform/get_field/",
            "saveURL": "/inplaceeditform/save/",
            "successText": "Successfully saved",
            "eventInplaceEdit": "dblclick",
            "disableClick": true,
            "autoSave": false,
            "unsavedChanges": "You have unsaved changes!",  // This is the only opts that can not be overwritten
            "enableClass": "enable",
            "fieldTypes": "input, select, textarea",
            "focusWhenEditing": true
        },
        configSelector: "inplaceeditform",
        formSelector: "form.inplaceeditform",
        enabled: false,
        inplaceeditfields: null,
        methods: {},
        extend: function (newMethods) {
            this.methods = $.extend(this.methods, newMethods);
        }
    };

    $.inplaceeditform.extend({
        init: function (opts) {
            var self = $.inplaceeditform;
            self.isMsIE = $.browser && $.browser.msie;
            self.opts = $.extend(self.opts, opts || {});
            self.inplaceeditfields = this;
            // Hack to event onbeforeunload in IE
            if (self.isMsIE) {
                if ($(document).on !== undefined) {
                    $(document).on("click", "a", function () {
                        window.couldCatch = true;
                        window.newLocation = $(this).attr("href");
                    });
                } else {
                    $("a").live("click", function () {
                        window.couldCatch = true;
                        window.newLocation = $(this).attr("href");
                    });
                }
            }
            this.each(function () {
                var configTag = $(this).find(self.configSelector);
                var config = configTag.attr();
                if (self.methods.getOptBool(config, self.opts, "disableClick")) {
                    $(this).click(self.methods.disableClickCallBack);
                }
                $(this).bind(self.methods.getOpt(config, self.opts, "eventInplaceEdit"), self.methods.eventInplaceEditCallBack);
            });
            window.onbeforeunload = self.methods.onBeforeUnloadEvent;
            return {
                enable: function () {
                    self.enabled = true;
                    self.inplaceeditfields.each(function () {
                        var configTag = $(this).find(self.configSelector);
                        var config = configTag.attr();
                        var enableClass = self.methods.getOpt(config, self.opts, "enableClass");
                        $(this).addClass(enableClass);
                    });
                },
                disable: function () {
                    self.enabled = false;
                    self.inplaceeditfields.each(function () {
                        var configTag = $(this).find(self.configSelector);
                        var config = configTag.attr();
                        var enableClass = self.methods.getOpt(config, self.opts, "enableClass");
                        $(this).removeClass(enableClass);
                    });
                }
            };
        },
        appendChild: function (node, text) {
            if (null === node.canHaveChildren || node.canHaveChildren) {
                node.appendChild(document.createTextNode(text));
            } else {
                node.text = text;
            }
        },
        autoSaveCallBack: function () {
            var self = $.inplaceeditform;
            var form = this.tag.parents(self.formSelector);
            var newValue = self.methods.getValue(form);
            if (newValue !== this.oldValue) {
                this.tag.parents(self.formSelector).find(".apply").click();
            } else {
                this.tag.parents(self.formSelector).find(".cancel").click();
            }
        },
        bind: function (func, that) {
            return function () {
                return func.apply(that, arguments);
            };
        },
        disableClickCallBack: function (ev) {
            var self = $.inplaceeditform;
            if (self.enabled) {
                ev.preventDefault();
            }
        },
        eventInplaceEditCallBack: function () {
            var self = $.inplaceeditform;
            if ($(this).data("ajaxTime")) {
                return false;
            }
            if (!self.enabled || !$(this).hasClass(self.opts.enableClass)) {
                return false;
            }
            var configTag = $(this).find(self.configSelector);
            var config = configTag.attr();
            $(this).data("ajaxTime", true);
            var data = self.methods.getDataToRequest(configTag);
            var extraConfig = configTag.data("extraConfig");
            if (extraConfig) {
                data = extraConfig(data);
            }
            data += "&__widget_height=" + $(this).innerHeight() + "px" + "&__widget_width=" + $(this).innerWidth() + "px";
            $.ajax({
                data: data,
                url: self.methods.getOpt(config, self.opts, "getFieldUrl"),
                type: "GET",
                async: true,
                dataType: "json",
                error: self.methods.bind(self.methods.treatmentStatusError, {"context": $(this)}),
                success: self.methods.bind(self.methods.inplaceGetFieldSuccess, {"that": this})
            });
        },
        getCSFRToken: function () {
            return csrf_token;
        },
        getDataToRequest: function (configTag) {
            var dataToRequest = "";
            var settings = configTag.attr();
            $.map(settings, function (value, key) {
                var data = "";
                if (dataToRequest !== "") {
                    data = "&";
                }
                data += key + "=" + value;
                dataToRequest += data;
            });
            var fontSize = configTag.parent().css("font-size");
            if (fontSize) {
                dataToRequest += "&font_size=" + fontSize;
            }
            return dataToRequest;
        },
        getDataToRequestUpload: function (configTag) {
            var dataToRequest = configTag.attr();
            var fontSize = configTag.parent().css("font-size");
            if (fontSize) {
                dataToRequest.font_size = fontSize;
            }
            return dataToRequest;
        },
        getOpt: function (config, genericOpts, opt) {
            return (config[opt.toLowerCase()] !== undefined && config[opt.toLowerCase()]) || genericOpts[opt];
        },
        getOptBool: function (config, genericOpts, opt) {
            var self = $.inplaceeditform;
            var val = self.methods.getOpt(config, genericOpts, opt);
            if (typeof val === "string") {
                val = parseInt(val);
            }
            return val;
        },
        getValue: function(form) {
            var applyButton = form.find(".apply");
            var getValue = applyButton.data("getValue"); // A hook
            var newValue;
            var field_id = form.find("span.field_id").html();
            if (getValue) {
                newValue = getValue(form, field_id);
            } else {
                newValue = form.find("#" + field_id).val();
            }
            return newValue;
        },
        inplaceApply: function () {
            var self = $.inplaceeditform;
            var form = $(this).parents(self.formSelector);
            if (form.data("ajaxTime")) {
                return
            }
            form.animate({opacity: 0.1}, function () {
                form.find(".apply, .cancel").invisible();
            });
            form.find("ul.errors").fadeOut(function () {
                $(this).remove();
            });
            var configTag = form.prev().find(self.configSelector);
            var config = configTag.attr();
            var data = self.methods.getDataToRequest(configTag);
            var value = self.methods.getValue(form);
            data += "&value=" + encodeURIComponent($.toJSON(value));
            var csrfmiddlewaretoken = self.methods.getCSFRToken();
            if (csrfmiddlewaretoken) {
                data += "&csrfmiddlewaretoken=" + csrfmiddlewaretoken;
            }
            form.data("ajaxTime", true);
            $.ajax({data: data,
                    url: self.methods.getOpt(config, self.opts, "saveURL"),
                    type: "POST",
                    async: true,
                    dataType: "text",
                    error: self.methods.bind(self.methods.treatmentStatusError, {"context": $(this)}),
                    success: self.methods.bind(self.methods.inplaceApplySuccess, {
                        "context": $(this),
                        "form": form,
                        "configTag": configTag
                    })
            });
            return false;
        },
        inplaceApplyUpload: function () {
            var self = $.inplaceeditform;
            var form = $(this).parents(self.formSelector);
            if (form.data("ajaxTime")) {
                return
            }
            form.animate({opacity: 0.1}, function() {
                form.find(".applyFile, .cancel").invisible();
            });
            form.find("ul.errors").fadeOut(function () {
                $(this).remove();
            });
            var configTag = form.prev().find(self.configSelector);
            var config = configTag.attr();
            var data = self.methods.getDataToRequestUpload(configTag);
            var csrfmiddlewaretoken = self.methods.getCSFRToken();
            if (csrfmiddlewaretoken) {
                data.csrfmiddlewaretoken = csrfmiddlewaretoken;
            }
            var value = self.methods.getValue(form);
            data.value = encodeURIComponent($.toJSON(value));
            form.data("ajaxTime", true);
            form.ajaxSubmit({url: self.methods.getOpt(config, self.opts, "saveURL"),
                             data: data,
                             async: true,
                             type: "POST",
                             method: "POST",
                             dataType: "json",
                             error: self.methods.bind(self.methods.treatmentStatusError, {"context": $(this)}),
                             success: self.methods.bind(self.methods.inplaceApplySuccess, {
                                "context": $(this),
                                "form": form,
                                "configTag": configTag
                             })
            });
            return false;
        },
        inplaceApplySuccess: function (response) {
            var self = $.inplaceeditform;
            var that = this.context;
            var form = this.form;
            form.data("ajaxTime", false);
            if (typeof response === "string") {
                if (self.isMsIE) {
                    response = self.methods.replaceAll(response, "'\\\\\"", "'");
                    response = self.methods.replaceAll(response, "\"'", "'");
                }
                try {
                    response = JSON.parse(response);
                } catch (errno) {
                    try {
                        response = eval("( " + response + " )");
                    } catch (errno2) {
                        alert(errno2);
                        return;
                    }
                }
            }
            self.methods.revertlinkInplaceEdit($(this.form).parents("a.linkInplaceEdit"));
            var configTag = this.configTag;
            var inplace_span = configTag.parents(".inplaceedit");
            var config = inplace_span.find(self.configSelector).attr();
            if (!response) {
                alert("The server is down");
            } else if (response.errors) {
                if (!self.methods.getOptBool(config, self.opts, "autoSave") || !parseInt(config.can_auto_save)) {
                    form.animate({opacity: 1}, function () {
                        form.find(".apply, .applyFile, .cancel").visible();
                    });
                } else {
                    form.animate({opacity: 1});
                }
                form.prepend("<ul class='errors'><li>" + response.errors + "</li></ul>");
            } else {
                that.parent().fadeOut();
                that.fadeIn();
                form.removeClass("inplaceeditformsaving");
                var config_html = "<" + self.configSelector;
                var attr;
                for (attr in config) {
                    config_html += ' ' + attr + '="' + config[attr] + '"';
                }
                config_html += "></" + self.configSelector + ">";
                inplace_span.html(response.value + config_html);
                inplace_span.css("display", "");
                self.methods.inplaceApplySuccessShowMessage(inplace_span, response);
                var applyFinish = that.data("applyFinish");
                if (applyFinish) {
                    applyFinish(that);
                }
                that.parent().remove();
            }
        },
        inplaceApplySuccessShowMessage: function (inplace_span) {
            var self = $.inplaceeditform;
            var configTag = inplace_span.find(self.configSelector);
            var config = configTag.attr();
            var successText = self.methods.getOpt(config, self.opts, "successText");
            if (successText) {
                var success_message = $("<ul class='success'><li>" + successText + "</li></ul>");
                inplace_span.prepend(success_message);
                inplace_span.removeClass(self.opts.enableClass);
                setTimeout(function () {
                    success_message.fadeOut(function () {
                        $(this).remove();
                        inplace_span.redraw();
                        if (self.enabled) {
                            inplace_span.addClass(self.opts.enableClass);
                        }
                    });
                }, 2000);
            }
        },
        inplaceCancel: function () {
            var self = $.inplaceeditform;
            self.methods.revertlinkInplaceEdit($(this).parents("a.linkInplaceEdit"));
            $(this).parent().prev().fadeIn();
            var cancelFinish = $(this).data("cancelFinish");
            if (cancelFinish) {
                cancelFinish(this);
            }
            $(this).parents(self.formSelector).remove();
            return false;
        },
        inplaceGetFieldSuccess: function(response) {
            var self = $.inplaceeditform;
            if (!response) {
                alert("The server is down");
            } else if (response.errors) {
                alert(response.errors);
            } else {
                var that = this.that;
                var configTag = $(that).find(self.configSelector);
                var config = configTag.attr();
                var tags = $(self.methods.removeStartSpaces(response.field_render));
                $(tags).insertAfter($(that));
                $(that).hide();
                var head = $("head")[0];
                try {
                    var medias = $(self.methods.removeStartSpaces(response.field_media_render));
                    var medias_preferred = medias.filter("[delay=delay]");
                    var medias_regular = medias.not("[delay=delay]");
                    $.map(medias_preferred, function (media, i) {
                        if (i === 0) {
                            self.methods.loadjscssfile(media);
                        } else {
                            setTimeout(function () {
                                self.methods.loadjscssfile(media);
                            }, 500);
                        }
                    });
                    if (medias_preferred.length === 0) {
                        $.map(medias_regular, function (media) {
                            self.methods.loadjscssfile(media);
                        });
                    } else {
                        setTimeout(function () {
                            $.map(medias_regular, function (media) {
                                self.methods.loadjscssfile(media);
                            });
                        }, 500);
                    }
                } catch (err) {
                }
                var links_parents = $(that).next().parents("a");
                if (links_parents.length > 0) {
                    $.map(links_parents, function (link) {
                        link = $(link);
                        var href = link.attr("href");
                        link.attr("hrefinplaceedit", href);
                        link.addClass("linkInplaceEdit");
                        link.removeAttr("href");
                    });
                }
                var applyButton = $(that).next().find(".apply");
                var cancelButton = $(that).next().find(".cancel");
                var applyFileButton = $(that).next().find(".applyFile");
                if (cancelButton.size()) {
                    cancelButton.click(self.methods.inplaceCancel);
                }
                if (applyButton.size()) {
                    applyButton.click(self.methods.inplaceApply);
                    $(that).next(self.formSelector).submit(self.methods.bind(self.methods.inplaceApply, applyButton));
                }
                if (applyFileButton.size()) {
                    applyFileButton.click(self.methods.inplaceApplyUpload);
                    $(that).next(self.formSelector).submit(self.methods.bind(self.methods.inplaceApplyUpload, applyFileButton));
                }
                var form = $(that).next(self.formSelector);
                var fieldTag = form.find(self.methods.getOpt(config, self.opts, "fieldTypes"));
                if (self.methods.getOptBool(config, self.opts, "focusWhenEditing")) {
                    fieldTag.focus();
                }
                if (self.methods.getOptBool(config, self.opts, "autoSave") && parseInt(config.can_auto_save)) {
                    applyButton.hide();
                    cancelButton.hide();
                    applyFileButton.hide();
                    var value = self.methods.getValue(form);
                    fieldTag.blur(
                        self.methods.bind(self.methods.autoSaveCallBack, {"oldValue": value,
                                                                          "tag": fieldTag})
                    );
                    $(that).next(self.formSelector).find("select").change(
                        self.methods.bind(self.methods.autoSaveCallBack, {"oldValue": value,
                                                                          "tag": fieldTag})
                    );
                }
            }
            $(that).data("ajaxTime", false);
        },
        loadjscssfile: function (media) {
            var self = $.inplaceeditform;
            var fileref;
            if (media.tagName === "SCRIPT") { //if filename is a external JavaScript file
                fileref = document.createElement("script");
                fileref.setAttribute("type", "text/javascript");
                if (media.src !== null && media.src !== "") {
                    fileref.setAttribute("src", media.src);
                } else {
                    self.methods.appendChild(fileref, media.innerHTML);
                }
            } else if (media.tagName === "LINK" && media.rel === "stylesheet") { //if filename is an external CSS file
                var type = media.type || "text/css";
                var rel = "stylesheet";
                var href = media.href;
                fileref = document.createElement("link");
                fileref.setAttribute("rel", rel);
                fileref.setAttribute("type", type);
                fileref.setAttribute("href", media.href);
            }

            if (typeof fileref !== "undefined") {
                document.getElementsByTagName("head")[0].appendChild(fileref);
            }
        },
        onBeforeUnloadEvent: function (event) {
            var msg = undefined;
            var self = $.inplaceeditform;
            if ($(self.formSelector).size()) {
                if (!self.isMsIE || (window.couldCatch && !(window.newLocation.indexOf("javascript:") === 0))) {
                    msg = self.opts.unsavedChanges;
                    if (event) {
                        // For IE and Firefox prior to version 4
                        event.returnValue = msg;
                    }
                }
            }
            window.couldCatch = false;
            window.newLocation = null;
            return msg;
        },
        removeStartSpaces: function (html) {
            // Remove the espaces and \n to the begin of the field_render
            return html.replace(/^( |\n)*/g, "");
        },
        replaceAll: function (txt, replace, with_this) {
            return txt.replace(new RegExp(replace, "g"), with_this);
        },
        revertlinkInplaceEdit: function (links_parents) {
            $.map(links_parents, function (link) {
                link = $(link);
                var href = link.attr("hrefinplaceedit");
                link.attr("href", href);
                link.removeClass("linkInplaceEdit");
                link.removeAttr("hrefinplaceedit");
            });
        },
        treatmentStatusError: function (response) {
            if (response.status === 0) {
                alert("The server is down");
            } else if (response.status === 403) {
                alert("Permission denied, please check that you are login");
            } else {
                alert("Some error. Status text =" + response.statusText);
            }
            this.context.next(".cancel").click();
            this.context.data("ajaxTime", false);
        }
    });
})(jQuery);
