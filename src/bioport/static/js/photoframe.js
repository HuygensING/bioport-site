
(function($) 
{
	$.fn.photoframe = function( options )
	{
		var defaults = {
			frames : 3, // auto generate this number of frames if none are present
			speed : 4000, // time between a cycle
			fadeOutSpeed : 600,  // 
			fadeInSpeed : 1200, // 
			stackSpeed : 1800, // delay after the crossfade to start with the next frame
			url: 'images.xml'  
		}
		
		var me = $(this);
		
		var opts = $.extend( defaults, options );
		
		// the image info
		var stack = new Array();
		
		// the id's of the frames
		var elements = new Array();
		
		// current element
		var elementIndex = 0;
		
		// bg element to pass
		var prevData ;
		
		// load up the image stack
		$.get( opts.url, function( response )
		{
			$('root',response).children('image').each(function()
			{
				stack.push({
					title: $(this).attr('title'),
					url: $(this).attr('url'),
					src: $(this).attr('src')
				});
			});
			
			
			// ready to go
			init();
			// start the endless loop
			setTimeout( crossFade, opts.speed );
			
		});
		
		
		function init()
		{
			// init
			me.each(function() {
				// the frames in which the images are loaded
				var frames = $(this).children('div');
				// if there aren't any, create them
				if( frames.length == 0 )
				{
					for( i=1; i<=opts.frames; i++ )
					{
						$(this).append('<div id="photoframe-'+i+'"></div>');
					}
					frames = $(this).children('div');
				}
				// place an imaga inside the frame and keep a record of frame id's
				frames.each(function(i)
				{
					createImage( $(this), i );
					elements.push( $(this).attr('id') );
				});
				//elements.reverse();
			});
			
			// add an onclick event on each div
			$('.bgImg').live('click', function()
			{
				window.location.href = $(this).attr('rel');
			});				
		}	
	
		
		function crossFade()
		{
			// start over
			if( elementIndex >= elements.length )
			{
				elementIndex = 0;
			}
			var cid = $('#'+elements[elementIndex]);
			var current = $('#'+elements[elementIndex]+' .bgImg:first');
			
			// we've reached the end, create new
			if( (elementIndex + 1) == elements.length )
			{
				var next = createImageElement( getNextImageInfo() );
				elementIndex++;
				setTimeout( crossFade, opts.speed );
			}
			else
			{
				var next = $('#'+elements[elementIndex+1]+' .bgImg:first').clone();
				elementIndex++;
				setTimeout( crossFade, opts.stackSpeed );
			}
			
			current.fadeOut( opts.fadeOutSpeed, function()
			{
				$(this).remove();
				setElement( next, cid );
				
			});
			
			
			
		}
		
		function setElement( element, parent )
		{
			element.css({
				'width' : parent.width(),
				'height' : parent.height(),
				'opacity' : 1
			})
			.hide()
			.appendTo( parent )
			.fadeIn( opts.fadeInSpeed );
		}



		function createImage( j )
		{
			// fetch one from the stack
			var c = stack.shift();
			stack.push(c);
			
			var d = createImageElement( c );
			
			d.css({
					'width' : j.width(),
					'height' : j.height(),
					'opacity' : 1
				});
	
			j.empty().append(d);
		}		
		
		function createImageElement( data )
		{
			return $('<img class="bgImg" />')
			.attr('src', data.src )
			.attr('title', data.title )
			.attr('alt', data.title)
			.attr('rel', data.url );
		}
		
		function XcreateImageElement( data )
		{
			return $('<div class="bgImg"></div>')
			.css({
				'background-image': 'url(' + data.src + ')',
				'opacity' : 0,
				'position' : 'absolute'
			})
			.attr('title', data.title )
			.attr('alt', data.title)
			.attr('rel', data.url );
		}
		
		/**
		 * Returns a new object with image data and places it down the stack
		 */
		function getNextImageInfo()
		{
			var c = stack.shift();
			stack.push(c);
			return c;
		}
		
	};
})(jQuery);