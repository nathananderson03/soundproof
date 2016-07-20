window.SoundproofPhotoSelect = function(){
    var spinner = null;

    var _pub = {
        'init':function(){
            spinner = new Spinner({
                'color':'#fff',
                'shadow':true,
            });
            $(document).on('click', '#images .photo', function() {
                // update selected element
                $('#images .photo').removeClass('selected');
                $(this).addClass('selected');

                show_preview();
            });

            $('.btn-print').on('click', print_photo);

            $('.btn-cancel').on('click', function(){
                $('#preview img').css('visibility','hidden');
                $('[data-mode]').attr('data-mode', 'select');
            });

            $('#preview img')
                .on('load', function(){
                    spinner.stop();
                    $(this).css('visibility','visible');
                })
                .on('error', function(){
                    alert('something went wrong, the selected image could not be printed');
                    $('.btn-cancel').trigger('click');
                });

            setInterval(function(){
                $.get('?action=images', function(data){
                    if($('[data-mode="preview"]').length){
                        return;
                    }
                    var el = $.parseHTML(data);
                    $('#images').replaceWith(el);
                });
            }, 5000);
        },
    };

    var print_photo = function() {
        var photo_id = $('.photo.selected').attr('data-id');
        var frame_id = $('.frame.selected').attr('data-id');

        // disable the print button
        $('.btn-print').prop('disabled', true);

        $.ajax({
            'url':'',
            'type':'post',
            'data': {
                'photo':photo_id,
                'frame':frame_id,
            },
            'headers':{
                'X-CSRFToken':$.cookie('csrftoken'),
            },
            'success':function(data, textStatus, jqXHR) {
                console.log('printing');
            },
            'complete':function(textStatus, jqXHR) {
                // reenable
                $('.btn-print').prop('disabled', false);
            },
        });
    };

    var show_preview = function(){
        var photo_id = $('.photo.selected').attr('data-id');
        var frame_id = $('.frame.selected').attr('data-id');

        spinner.spin($('#preview')[0]);
        var img = $('#preview img');
        img.css('visibility','hidden');
        img.attr('src', '?action=preview&photo='+photo_id+'&frame='+frame_id);

        $('[data-mode]').attr('data-mode', 'preview');
    };

    return _pub;
}();
$(SoundproofPhotoSelect.init);
