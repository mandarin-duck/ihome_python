function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }

        var data = {
            "mobile": mobile,
            "password": passwd
        };

        $.ajax({
            url: "/api/v1.0/sessions",
            type: "post",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resq) {
                if(resq.errno == 0){
                    location.href="/";
                }else {
                    $("#password-err span").html(resq.errmsg);
                    $("#password-err").show();
                }
            }
        })
    });
})