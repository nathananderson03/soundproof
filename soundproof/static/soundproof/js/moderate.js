window.SoundproofModeration = function(){
    var _pub = {
        'init':function(){
            // jquery docs suck
            // so welcome to code duplication
            $('[data-moderate-image]').on('click', moderate_image);
        },
    };
    var moderate_image = function(ev) {
        ev.preventDefault();
        var img = $(this);
        var id = img.attr("data-image-id");
        var slug = img.attr("data-display-slug");
        var approve = !img.hasClass('image-whitelisted');
        console.log(approve);

        console.log(slug, id, approve);
        $.ajax({
            'url':'/moderate/'+slug,
            'type':'post',
            'data': {
                'approved':approve,
                'img_id':id,
            },
            'headers':{
                'X-CSRFToken':$.cookie('csrftoken'),
            },
            'success':function(data, textStatus, jqXHR) {
                console.log(img);
                console.log('success');
                console.log(img.text());
                if(approve) {
                    // approved
                    console.log('whitelisted');
                    img.addClass('image-whitelisted');
                    img.removeClass('image-blacklisted');
                    img.addClass('btn-primary');
                    img.removeClass('btn-danger');
                    img.text("Reject");
                } else {
                    // blacklisted
                    console.log('blacklisted');
                    img.removeClass('image-whitelisted');
                    img.addClass('image-blacklisted');
                    img.removeClass('btn-primary');
                    img.addClass('btn-danger');
                    img.text("Approve");
                }
                console.log(img.text());
            },
        });
    };
    return _pub;
}();
$(SoundproofModeration.init);
