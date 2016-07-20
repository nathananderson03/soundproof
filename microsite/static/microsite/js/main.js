$(function(){
    $('#videos .video-controls span').on('click',function(){
        var ix = 1+$(this).index();
        $('#videos iframe').hide();
        $('#videos iframe:nth-child('+ix+')').show();
    });
    var first_id = null;
    var loading = false;
    var populate_feed = function(n){
        loading = true;
        var api_url = 'http://soundproof.alhazan.ath.cx/api/json-images';
        var feed_name = $('#feed').attr('data-feed');
        $.ajax({
            'url':api_url,
            'data':{
                'display_id':5, //TODO
                'lt_id':first_id,
                'count':n,
            },
            'dataType':'json',
            'success':function(data){
                $.each(data,function(n, item){
                    var caption_html = item.meta.caption.replace(/#\S+/g,
                        function(m) {
                            return '<strong>'+m+'</strong>';
                        }
                    );
                    var wut1 = String.fromCharCode(55356);
                    var wut2 = String.fromCharCode(55357);
                    caption_html = caption_html.replace(new RegExp(wut1,'g'),'');
                    caption_html = caption_html.replace(new RegExp(wut2,'g'),'');
                    var clone = $('[data-template="feed-item"]').clone();
                    clone.removeAttr('data-template');
                    clone.find('.mainlink').attr('href', item.url);
                    clone.find('.img').attr('src',item.img);
                    clone.find('.text').html(caption_html);
                    clone.find('.age').text(item.age);
                    clone.find('.author-name').text(item.meta.user);
                    clone.find('.author-handle').text('@'+item.meta.user);
                    clone.find('.mug').attr('src',item.user_mug);
                    $('#feed').append(clone);
                    if(first_id == null){
                        first_id = item.id;
                    }
                    else {
                        first_id = Math.min(first_id, item.id);
                    }
                });
                loading = false;
                reflow_feed();
            },
        });
    };
    var reflow_feed = function(){
        var feed = $('#feed');

        var min_width = 300;
        var h_margin = 10;
        var v_margin = 10;

        var col_count = Math.floor(feed.width() / min_width);
        var cols = [];
        for (var n = 0; n < col_count; n++) {
            cols.push(n);
        }
        var col_width = (feed.width() - h_margin * (col_count+1))/col_count;
        $('#feed > div').each(function(n, el){
            var col_num = n % col_count;
            $(this).css({
                'width': col_width,
                'left':h_margin*(1+col_num) + col_num * col_width,
                'top':cols[col_num],
            });
            $(this).find('.img').css({'height':col_width});
            cols[col_num] += $(this).height() + v_margin;
        });
        $('#feed').css({
            'height':Math.max.apply(null, cols),
        });
    };
    var $window = $(window);
    var $footer = $('#footer');
    var handle_scroll = function(){
        if(loading){
            return;
        }
        var window_bottom = $window.scrollTop() + $window.height();
        var trigger = $footer.offset().top - 500;
        if(window_bottom > trigger){
            populate_feed(10);
        }
    };
    populate_feed(20);
    reflow_feed();
    $window.on('resize',reflow_feed);
    $window.on('scroll',handle_scroll);
});
