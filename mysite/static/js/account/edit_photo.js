var csrf_token = null;
var width = null;

function set_callback_for_image_upload(token){
    $("#edit_photo").on("submit", upload_image);
    csrf_token = token;
    width = $("#progressBar").width();
    $('#clear_message').on("click", hide_notification);
}

function hide_notification(event){
    $("#notification").hide();
    return false;
}

function update(evt){
    $("#progressBar").css("display", "");
    var percent = Math.floor(evt.loaded/evt.total * 100);
    var progressBarWidth = Math.floor((percent * width) / 100);
    $("#progressBar").find('div').animate({ width: progressBarWidth }, 500).html(percent + "%&nbsp;");
}

function upload_image(event){
    $("#progressBar").find("div").css("width", "0px");
    event = event || window.event;
    // Prevent the default form action i.e. loading of a new page
    if(event.preventDefault){ // W3C Variant
        event.preventDefault();
    }
    else{ // IE < 9
        event.returnValue = false;
    }
    $.ajax({
            url: "/account/edit/photo/do",
            type: "POST",
            data: new FormData($('#edit_photo')[0]), 

            success : function(data){
                $("#notification_message").html("Image Saved Successfully");
                $("#notification").css("display", "block");
                $("#progressBar").find("div").css("width", "0px");
                $("#progressBar").css("display", "none");
                $("#profileimage").attr("src", data);
            },

            xhr: function(){
                // get the native XmlHttpRequest object
                var xhr = $.ajaxSettings.xhr() ;
                // set the onprogress event handler
                xhr.upload.onprogress = update,
                // set the onload event handler
                xhr.upload.onload = function(){ } ;
                // return the customized object
                return xhr ;
            },

            enctype: 'multipart/form-data',
            processData: false,
            contentType: false,
            cache: false,
            headers: { "X-CSRFToken": csrf_token }
    });
}
    
