require 'net/http'
require 'uri'
require 'md5'  

# Set up include path correctly
$:.unshift(File.dirname(__FILE__)) unless $:.include?(File.dirname(__FILE__)) || $:.include?(File.expand_path(File.dirname(__FILE__)))

# This module encapsulates functionality (ad requests, analytics requests) provided by AdMob. See README.txt for usage.
module AdMob
  
  GEM_VERSION = '1.1.1'

  ENDPOINT = URI.parse('http://r.admob.com/ad_source.php')
  PUBCODE_VERSION = '20090106-RUBY-8708a7ab5f2b70b6'
  DEFAULT_TIMEOUT = 1.0

  # Make an AdMob ad/analytics request. The first param is the request variable from Rails; the second is a unique session
  # identifier. In general, requests should always be of the form <tt><%= AdMob::request(request, session.session_id, ...) %></tt>.
  # Regardless of how many times AdMob::request is called, only one analytics call will be made per page load.
  # The remaining params set optional features of the request. Params that can be set are:
  #
  # [<tt>:publisher_id</tt>] your admob publisher_id, a default can be set using <tt>AdMob::config {|c| c.publisher_id = "YOUR_PUBLISHER_ID"}</tt>
  # [<tt>:analytics_id</tt>] your admob analytics_id, a default can be set using <tt>AdMob::config {|c| c.analytics_id = "YOUR_ANALYTICS_ID"}</tt>
  # [<tt>:ad_request</tt>] whether to make an ad request, defaults to true
  # [<tt>:analytics_request</tt>] whether to make an analytics request, defaults to true
  # [<tt>:encoding</tt>] char encoding of the response, either "UTF-8" or "SJIS", defaults to UTF-8
  # [<tt>:markup</tt>] your site's markup, e.g. "xhtml", "wml", "chtml"
  # [<tt>:postal_code</tt>] postal code of the current user, e.g. "94401"
  # [<tt>:area_code</tt>] area code of the current user, e.g. "415"
  # [<tt>:coordinates</tt>] lat/long of the current user, comma separated, e.g. "37.563657,-122.324807"
  # [<tt>:dob</tt>] date of birth of the current user, e.g. "19800229"
  # [<tt>:gender</tt>] gender of the current user, e.g. "m" or "f"
  # [<tt>:keywords</tt>] keywords, e.g. "ruby gem admob"
  # [<tt>:search</tt>] searchwords (much more restrictive than keywords), e.g. "ruby gem admob"
  # [<tt>:title</tt>] title of the page, e.g. "Home Page"
  # [<tt>:event</tt>] the event you want to report to analytics, e.g. "reg_success"
  # [<tt>:text_only</tt>] if set to true, don't return a banner ad for this request
  # [<tt>:test</tt>] whether this should issue a test ad request, not a real one
  # [<tt>:timeout</tt>] override the default timeout value for this ad request in seconds, e.g. 2
  # [<tt>:raise_exceptions</tt>] whether to raise exceptions when something goes wrong (defaults to false); exceptions will all be instances of AdMob::Error; a default can be set using <tt>AdMob::config {|c| c.raise_exceptions = true}</tt>
  def self.request(request, session_id, params = {})
    raise_exceptions = params[:raise_exceptions].nil? ? AdMob::Defaults.raise_exceptions : params[:raise_exceptions]
    
    if raise_exceptions and !params[:cookie_domain].nil?
      raise AdMob::Error.new("Cannot set cookie_domain in AdMob::request(), set the cookie_domain in the call to AdMob::set_cookie()")
    end
    
    if raise_exceptions and !params[:cookie_path].nil?
      raise AdMob::Error.new("Cannot set cookie_path in AdMob::request(), set the cookie_path in the call to AdMob::set_cookie()")
    end
    
    # Build the post request
    post_data = self.build_post_data(request, session_id, params)
    if post_data.nil?
      raise AdMob::Error.new("AdMob::request called as neither an ad nor an analytics request") if raise_exceptions
      return ''
    end
    
    # Send request
    req = Net::HTTP::Post.new(ENDPOINT.path)
    req.set_form_data(post_data)
    conn = Net::HTTP.new(ENDPOINT.host, ENDPOINT.port)
    timeout = params[:timeout] || AdMob::Defaults.timeout || DEFAULT_TIMEOUT
    conn.read_timeout = timeout
    conn.open_timeout = timeout
    begin
      start = Time.now.getutc.to_f
      response = conn.start {|http| http.request(req)}
      contents = response.body
    rescue Timeout::Error => te
      raise AdMob::Error.new("AdMob::request timed out; timeout was #{timeout}, elapsed time was #{Time.now.to_f - post_data['z']}") if raise_exceptions
    rescue
      raise AdMob::Error.new("AdMob::request encountered unexpected exception #{$!}") if raise_exceptions
    ensure
      contents ||= ''
      lt = Time.now.getutc.to_f - start
    end
    
    # If appropriate, add the analytics pixel
    if !request.env['admob_pixel_sent']
      request.env['admob_pixel_sent'] = true
      contents << '<img src="http://p.admob.com/e0?'
      contents << "rt=#{post_data['rt']}&amp;"
      contents << "z=#{post_data['z']}&amp;"
      contents << "a=#{post_data['a']}&amp;"
      contents << "s=#{post_data['s']}&amp;"
      contents << "o=#{post_data['o']}&amp;"
      contents << "lt=%0.4f&amp;" % lt
      contents << "to=#{timeout}"
      contents << '" alt="" width="1" height="1"/>'
    end
    
    contents
  end

  # This function should be called from an ActionController to set a cookie on behalf of AdMob.
  # If you need to override the default cookie domain or cookie path, pass these as optional parameters to AdMob::set_cookie(). 
  #   AdMob::set_cookie(request, cookies, :cookie_domain => 'example.com', :cookie_path => '/videos')
  # You can NOT pass cookie_domain or cookie_path as optional parameters to AdMob::request()
  # AdMob recommends using a before_filter in your ActionController::Base class (usually in app/controllers/application.rb) to call set_cookie on each request.
  # Here is a sample application.rb.
  #   require 'admob'
  #   # Filters added to this controller apply to all controllers in the application.
  #   # Likewise, all the methods added will be available for all controllers.
  #
  #   class ApplicationController < ActionController::Base
  #     before_filter :admob_set_cookie
  #     
  #     def admob_set_cookie
  #       AdMob::set_cookie(request, cookies)
  #     end
  #   end
  def self.set_cookie(request, cookies, params = {})
    # don't make a new cookie if one already exists
    return if request.env['admobuu'] or cookies[:admobuu]
    
    # make a new cookie
    value = MD5.hexdigest(rand().to_s + request.user_agent + request.remote_ip + Time.now.to_f.to_s)
    new_cookie = { :value    => value,
                   :expires  => Time.at(0x7fffffff), # end of 32 bit time
                   :path     => params[:cookie_path] || AdMob::Defaults.cookie_path || "/" }
    
    domain = params[:cookie_domain] || AdMob::Defaults.cookie_domain
    if domain
      domain = '.' + domain if domain[0].chr != '.'
      new_cookie[:domain] = domain
    end
    cookies[:admobuu] = new_cookie
    
    # make this cookie visible to the current page
    request.env['admobuu'] = value
  end
  
  # Provides access to AdMob config, used for setting default request info.
  # Currently, can be used to set defaults for: publisher_id, analytics_id, ad encoding, request timeout, cookie_domain, cookie_path
  # and whether exceptions are raised when something goes wrong.
  # For example, in environment.rb:
  #  require 'admob'
  #  AdMob::config do |c|
  #    c.publisher_id = 'YOUR_DEFAULT_PUBLISHER_ID'
  #    c.analytics_id = 'YOUR_DEFAULT_ANALYTICS_ID'
  #    c.encoding = 'SJIS'
  #    c.timeout = 3
  #    c.raise_exceptions = true
  #    c.cookie_domain = 'example.com' # this can also be passed to AdMob::set_cookie() but not AdMob::request()
  #    c.cookie_path = '/' # this can also be passed to AdMob::set_cookie() but not AdMob:request()
  #  end
  def self.config
    yield AdMob::Defaults
  end

  # Simple exception class used for all AdMob exceptions. By default, exceptions are never raised.
  # To enable raising of exceptions, set parameter :raise_exceptions => true for a request, or
  # set a default using AdMob::config (see AdMob::config documentation).
  class Error < StandardError
  end

private
  
  # Stores default values for AdMob requests. Set these defaults via AdMob::config.
  class Defaults
    class << self
      attr_accessor :publisher_id, :analytics_id, :encoding, :timeout, :raise_exceptions, :cookie_domain, :cookie_path
    end
  end

  def self.build_post_data(request, session_id, params)
    # Gather basic data
    publisher_id = params[:publisher_id] || AdMob::Defaults.publisher_id
    analytics_id = params[:analytics_id] || AdMob::Defaults.analytics_id
    test = params[:test].nil? ? (RAILS_ENV == 'test') : params[:test]
    encoding = params[:encoding] || AdMob::Defaults.encoding

    # Determine the type of request
    analytics_request = (params[:analytics_request] != false) && (!analytics_id.nil?) && (!analytics_id.strip.empty?) && (!request.env['admob_pixel_sent'])
    ad_request = (params[:ad_request] != false) && (!publisher_id.nil?) && (!publisher_id.strip.empty?)

    case [ad_request, analytics_request]
    when [false, false] then return nil
    when [true, false] then request_type = 0
    when [false, true] then request_type = 1
    when [true, true] then request_type = 2
    end
    
    # Build the basic request
    post_data = {
      'rt'        => request_type,
      'z'         => Time.now.getutc.to_f,
      'u'         => request.user_agent,
      'i'         => request.remote_ip,
      'p'         => request.request_uri,
      't'         => MD5.hexdigest(session_id),
      'v'         => PUBCODE_VERSION,
      'o'         => request.cookies['admobuu'][0] || request.env['admobuu'],
      's'         => publisher_id,
      'a'         => analytics_id,
      'ma'        => params[:markup],
      'd[pc]'     => params[:postal_code],
      'd[ac]'     => params[:area_code],
      'd[coord]'  => params[:coordinates],
      'd[dob]'    => params[:dob],
      'd[gender]' => params[:gender],
      'k'         => params[:keywords],
      'search'    => params[:search],
      'f'         => 'html',
      'title'     => params[:title],
      'event'     => params[:event]
    }

    # Add in headers
    ignore_headers = Set['HTTP_PRAGMA', 'HTTP_CACHE_CONTROL', 'HTTP_CONNECTION',
        'HTTP_USER_AGENT', 'HTTP_COOKIE', 'ADMOB_PIXEL_SENT', 'ADMOBUU']
    request.env.each {|k,v| post_data["h[#{k}]"] = v unless ignore_headers.include?(k.upcase.gsub(/-/,'_'))}

    # Add in optional data
    post_data['e'] = encoding if encoding
    post_data['y'] = 'text' if params[:text_only]
    post_data['m'] = 'test' if test
    
    # Don't send anything that's nil (but send if empty string)
    post_data.delete_if {|k,v| v.nil?}
  end

end
