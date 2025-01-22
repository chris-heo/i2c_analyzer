/**
 * d.js - too lazy for a proper name.
 * This class offers shortcuts to many DOM manipulations
 */
class d
{
    static d = document;
    static w = window;
    /**
     * Alias of document.getElementById
     * @param {string} i Element id
     * @returns {HtmlElement} Found element
     */
    static ebi(i) { return document.getElementById(i); }

    /**
     * Alias of document.getElementsByName
     * @param {string} n Element name
     * @returns {HtmlCollection} Collection of found Elements
     */
    static ebn(n) { return document.getElementsByName(n); }

    /**
     * Returns the first element found by document.getElementsByName
     * @param {string} n Element name
     * @returns {HtmlElement} First found Element
     */
    static febn(n) { return document.getElementsByName(n)[0]; }

    /**
     * Creates an HtmlElement, alias of document.createElement with some extra steps
     * @param {string} n tagName of the new HtmlElement
     * @param {object} a Attributes of element, @see d.sa
     * @returns {HtmlElement} Created HtmlElement
     */
    static ce(n, a) 
    {
        var e = document.createElement(n); 
        if(a !== undefined)
        {
            d.sa(e, a);
        }
        return e;
    }

    /**
     * Alias of document.createDocumentFragment
     * @param {array} list of elements to be added to the documentFragment
     * @returns {DocumentFragement} An empty DocumentFragment
     */
    static cdf(a)
    {
        let f = document.createDocumentFragment();
        if(a != undefined)
        {
            a.forEach(e => d.ac(f, (typeof e === "string") ? d.ctn(e) : e));
        }
        return f;
    }

    /**
     * Alias of document.createTextNode
     * @param {string} n Text content of the TextNode
     * @returns {TextNode} The newly create TextNode
     */
    static ctn(n) { return document.createTextNode(n); }

    /**
     * Appends a child to a parentNode, sophisticated alias of p.appendChild(c)
     * @param {HtmlElement} p ParentNode where the child is attached to
     * @param {HtmlElement|string|Number|Array} c Child to be attached to parentNode @see d.sna2f
     * @returns {HtmlElement} HtmlElement of the appended child (c)
     */
    static ac(p, c) { return p.appendChild(d.sna2f(c)); }

    /**
     * Appends a child before the given sibling
     * @param {HtmlElement} s Sibling of which the child is attached before
     * @param {HtmlElement|string|Number|Array} c Child to be attached to parentNode @see d.sna2f
     * @returns {HtmlElement} HtmlElement of the appended child (c)
     */
    static acb(s, c) { return s.parentNode.insertBefore(d.sna2f(c), s); }

    /**
     * Appends a child after the given sibling
     * @param {HtmlElement} s Sibling of which the child is attached after
     * @param {HtmlElement|string|Number|Array} c Child to be attached to parentNode @see d.sna2f
     * @returns {HtmlElement} HtmlElement of the appended child (c)
     */
    static aca(s, c) {
        if(s.nextSibling == null)
            return s.parentNode.appendChild(d.sna2f(c));
        return s.parentNode.insertBefore(d.sna2f(c), s.nextSibling); 
    }

    /**
     * Appends a child to a parentNode, sophisticated alias of p.appendChild(c)
     * @param {HtmlElement} p ParentNode where the child is attached to
     * @param {HtmlElement|string|Number|Array} c Child to be attached to parentNode @see d.sna2f
     * @returns {HtmlElement} HtmlElement of the parent node (p)
     */
    static acp(p, c)
    {
        if(typeof(p) == "string")
            p = d.ce(p);
        p.appendChild(d.sna2f(c));
        return p;
    }

    /**
     * Alias of e.firstChild
     * @param {HtmlElement} e Parent HtmlElement
     * @returns {HtmlElement} HtmlElement of the first child in e
     */
    static fc(e) { return e.firstChild; }

    /**
     * Alias of e.lastChild
     * @param {HtmlElement} e Parent HtmlElement
     * @returns {HtmlElement} HtmlElement of last child in e
     */
    static lc(e) { return e.lastChild; }

    /**
     * Returns the text content of the given HtmlElement
     * @param {HtmlElement} e HtmlElement of which the textContent shall be retrieved
     * @returns {string} Text content of HtmlElement
     */
    static tc(e) { return e.textContent; }

    /**
     * Removes HtmlElement with self-awareness of parentNode
     * @param {HtmlElement} e HtmlElement that shall be removed from the document/element
     * @returns {HtmlElement} Removed HtmlElement
     */
    static re(e) { return e.parentNode == null ? e : e.parentNode.removeChild(e); }

    /**
     * Removes the last child node of an HtmlElement
     * @param {HtmlElement} e HtmlElement of which the last child shall be removed
     * @returns Returns the removed child node or null if there was none
     */
    static rlc(e)
    {
        if(e.lastChild) return e.removeChild(e.lastChild);
        return null;
    }

    /**
     * Removes all child nodes from given HtmlElement
     * @param {HtmlElement} e HtmlElement of which all childs shall be removed
     * @returns {HtmlElement} provided HtmlElement (e)
     */
    static rac(e)
    {
        while(e.hasChildNodes())
        {
            e.removeChild(e.lastChild);
        }
        return e;
    }

    /**
     * Checks if the given object is an instance of any class
     * @param {object} e Object to be checked
     * @returns {bool} True if object is an instance of a class, false if not
     */
    static iio(e)
    {
        try
        {
            return e.constructor.__proto__.prototype.constructor.name ? true : false;
        }
        catch(b)
        {
            return false;
        }
    }

    /**
     * Concatenates all elements and strings into one documentFragment
     * @param {Array} a Array of HtmlElements and strings
     * @returns DocumentFragment containing elements given in a
     * @deprecated integrated in @see d.cdf
     */
    static ces(a)
    {
        var f = d.cdf();
        for(var i = 0; i < a.length; i++)
        {
            var e = a[i];
            if(typeof e === "string")
            {
                d.ac(f, d.ctn(e));
            }
            else
            {
                d.ac(f, e);
            }
        }
        return f;
    }

    /**
     * Sets attributes to given object
     * @param {HtmlElement|object} o target for attributes
     * @param {Object} a Hierarchical object with attributes to be set to an object
     * @returns provided object in parameter o
     * @example d.sa(d.ce("div"), {"className" : "foobar", style" : {"fontFamily" : "fixed"}});
     */
    static sa(o, a)
    {
        if(o instanceof Object)
        {
            for(var n in a)
            {
                if(a[n] instanceof Object)
                {
                    d.sa(o[n], a[n]);
                }
                else
                {
                    o[n] = a[n];
                }
            }
        }
        return o;
    }

    //create select
    /**
     * Creates a select element with given options
     * @param {Array[]} o 2-dimensional array of options, 2. dimension contains option title + optional value + selected status (bool)
     * @returns {HtmlElement} HtmlElement of select element
     * @example d.cs([["Option 0"], ["Option one", "option_1"], ["Option 3", undefined, true]])
     */
    static cs(o)
    {
        var s = d.ce("select");
        for(var i = 0; i < o.length; i++)
        {
            var e = d.ac(s, d.acp(d.ce("option"), d.ctn(o[i][0])));
            if(o[i][1] !== undefined &&  o[i][1] !== null) { e.value = o[i][1]; }
            if(o[i][2] === true) { e.selected = true; }
        }
        return s;
    }

    /**
     * Returns the result of a single node selected by the given XPath
     * @param {string} p XPath of objects to be selected
     * @param {HtmlElement} c Context for the XPath (target element)
     * @returns {HtmlElement|object} Found object
     */
    static ebx(p, c)
    {
        if(c == undefined) { c = document; }
        return document.evaluate(p, c, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    }

    /**
     * Returns the result of nodes selected by the given XPath
     * @param {string} p XPath of objects to be selected
     * @param {HtmlElement} c Context for the XPath (target element)
     * @returns {Array} Found objects
     */
    static ebxm(p, c)
    {
        if(c == undefined) { c = document; }
        var ret = [];
        var res = document.evaluate(p, c, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        for ( var i=0 ; i < res.snapshotLength; i++)
        {
            ret.push(res.snapshotItem(i));
        }
        return ret;
    }

    /**
     * Returns the offsets of the given element
     * @param {HtmlElement} e HtmlElement of which the offsets shall be calculated
     * @returns {object} keys: offsetLeft, offsetTop, offsetHeight, offsetWidth
     */
    static eo(e)
    {
        var left = 0;
        var top = 0;
        var height = e.offsetHeight;
        var width = e.offsetWidth;
        if(e.offsetParent && e.style.position != "absolute") {
            do {
                left += e.offsetLeft;
                top += e.offsetTop;
                if(e.tagName == "BODY") { break; }
            } while (e = e.offsetParent);
        }
        return { "offsetLeft" : left, "offsetTop" : top, "offsetHeight" : height, "offsetWidth" : width };
    }

    /**
     * Adds an event listener to the given object and event
     * @param {HtmlElement} o object to which the event listerner shall be attached
     * @param {string} e event to be attached (e.g. "click")
     * @param {function} f callback function for the event
     */
    static ea(o, e, f)
    {
        if(typeof(o) == "string") { o = d.ebi(o); }
        if(o.addEventListener)
        {
            o.addEventListener(e, f, false);
        }
        else if(o.attachEvent)
        {
            o.attachEvent('on' + e, f);
        }
        return o;
    }

    /**
     * Removes an event listener to the given object and event
     * @param {HtmlElement} o object to which the event listerner shall be attached
     * @param {string} e event to be attached (e.g. "click")
     * @param {function} f callback function for the event
     */
    static er(o, e, f) {
        if(o.removeEventListener)
        {
            return o.removeEventListener(e, f);
        }
        else if(o.detachEvent)
        {
            o.detachEvent('on' + e, f);
        }
    }

    /**
     * Removes all elements with the given value from the array
     * @param {array} a the array from with the element shall be removed
     * @param {object} v value in the array that shall be removed
     * @returns {array} the reference of a
     */
    static arbv(a, v) {
        var i = 0;
        while((i = a.indexOf(v)) != -1)
        {
            a.splice(i, 1);
        }
        return a;
    }

    /**
     * Converts a string, number or array to a DocumentFragment
     * @param {string|number|Array} o Element to be attached to a new DocumentFragment
     * @returns {DocumentFragment} A DocumentFragment containing all elements provided in o
     */
    static sna2f(o)
    {
        if(o == undefined)
            o = "";
        if(Array.isArray(o))
        {
            let df = d.cdf();
            o.forEach((e) => d.ac(df, e));
            return df;
        }
        let ot = typeof(o);
        if(ot == "string" || ot == "number")
            return d.ctn(o);
        return o;
    }

    /**
     * Creates a table row with cells of the content given in ca
     * @param {array} ca Content array for the row, array elements can be text, numbers or HtmlElements
     * @param {bool} h True if the row is a header row (th), false if not (td)
     * @param {object} cs attributes to be assigned to the cell elements, @see d.sa
     * @returns {HtmlElement} HtmlElement of the table row
     */
    static a2tr(ca, h, cs)
    {
        let tr = d.ce("tr");
        let ct = (h == true) ? "th" : "td";
        ca.forEach(i => {
            if(i instanceof HTMLElement && (i.tagName == "TH" || i.tagName == "TD"))
            {
                d.ac(tr, i);
            }
            else
            {
                let ce = d.ce(ct, cs);
                d.ac(tr, d.acp(ce, i));
            }
        });

        return tr;
    }

    /**
     * Adds a css class to the given HtmlElement
     * @param {HtmlElement} e HtmlElement where the css class shall be added
     * @param {string} c ClassName that shall be added to the element
     * @returns {HtmlElement} Reference to e
     */
    static ca(e, c)
    {
        if(e.classList)
        {
            e.classList.add(c);
            return e;
        }
        let arr = e.className.split(" ");
        if (arr.indexOf(c) == -1)
        {
            e.className += " " + c;
        }
        return e;
    }

    /**
     * Removes a css class from the given HtmlElement
     * @param {HtmlElement} e HtmlElement where the css class shall be removed
     * @param {string} c ClassName that shall be removed to the element
     * @returns {HtmlElement} Reference to e
     */
    static cr(e, c)
    {
        if(e.classList)
        {
            e.classList.remove(c);
            return e;
        }
        let tmp = e.className.split(" ");
        while(true)
        {
            let i = tmp.indexOf(c);
            if(i == -1) break;
            tmp.splice(i, 1);
        }
        e.className = tmp;
        return e;
    }

    /**
     * Creates a datalist with the provided values
     * @param {string} i id of the datalist
     * @param {array} o Options for the datalist
     * @returns {HtmlElement} HtmlElement of the datalist with the provided vlaues
     */
    static cdl(i, o)
    {
        let l = d.ce("datalist", { "id" : i });
        for (let x = 0; x < o.length; x++) {
            d.ac(l.options, d.ce("option", { "value" : o[x] }));
        }
        return l;
    }

    /**
     * Creates a random string
     * @param {number} l length of the random string
     * @param {string} cs character set for the random string, @default [A-Za-z0-9]
     * @returns {string} Random string with the length l and character set cs
     */
    static rndc(l, cs)
    {
        let r = "";
        cs = cs || "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        for(let i = 0; i < l; i++ ) {
            r += cs[Math.floor(Math.random() * cs.length)];
        }
        return r;
    }

    /**
     * Creates a checkbox with an associated label
     * @param {string} l Label text
     * @returns {array} Array containing the label and the checkbox
     */
    static ccbl(l)
    {
        let cb = d.ce("input", { "type" : "checkbox" });
        return [ d.acp(d.ce("label"), [ cb, d.ctn(l) ]), cb ];
    }

    /**
     * Crates a radio button with an associated label
     * @param {string} n Name of the radio button group
     * @param {string} v Value of the radio button
     * @param {string} l Label text
     * @returns {array} Array containing the label and the radio button
     */
    static ccbr(n, v, l)
    {
        let cb = d.ce("input", { "type" : "radio", "name" : n, "value" : v});
        return [ d.acp(d.ce("label"), [ cb, d.ctn(l) ]), cb ];
    }

    /**
     * Copy text to the clipboard, must be called by user activity
     * @param {string} t Text to be copied to the clipboard
     */
    static ccb(t)
    {
        let cb = navigator.clipboard;
        if(cb && cb.writeText)
        {
            navigator.clipboard.writeText(t);
        }
        else
        {
            const e = d.ce("textarea");
            e.value = t;
            d.ac(d.d.body, e);
            e.select();
            document.execCommand("copy");
            d.re(e);
        }
    }

    /**
     * Copy the contents of an HtmlElement to the clipboard, must be called by user activity
     * @param {HtmlElement} e HtmlElement to be copied to the clipboard
     */
    static tcb(e)
    {
        var body = document.body, range, sel;
        if (document.createRange && window.getSelection)
        {
            range = document.createRange();
            sel = window.getSelection();
            sel.removeAllRanges();
            try
            {
                range.selectNodeContents(e);
                sel.addRange(range);
            }
            catch (ex)
            {
                range.selectNode(e);
                sel.addRange(range);
            }
        }
        else if (body.createTextRange)
        {
            range = body.createTextRange();
            range.moveToElementText(e);
            range.select();
        }
        document.execCommand("copy");
        sel.removeAllRanges();
    }

    /**
     * Offers text/data as file download
     * @param {string} fn Name of the file offered as download
     * @param {string} te Text content of the file
     * @param {string} mt mimetype of the file @default text/plain
     */
    static df(fn, te, mt)
    {
        var e = d.ce('a');
        mt = mt || "text/plain";
        e.setAttribute("href", "data:" + mt + ";charset=utf-8," + encodeURIComponent(te));
        e.setAttribute("download", fn);
        e.style.display = "none";
        d.ac(d.d.body, e);
        e.click();
        d.re(e);
    }

    static gmp(evt) 
    {
        var rect = evt.target.getBoundingClientRect();
        return {
            x: evt.clientX - rect.left,
            y: evt.clientY - rect.top
        };
      }
}

/*function getCSSRule(ruleName, deleteFlag) {
    ruleName = ruleName.toLowerCase();
    var lastRule = null; var lastRuleCnt = 0;
    if(document.styleSheets) {
        for(var i=0; i<document.styleSheets.length; i++) {
            var styleSheet=document.styleSheets[i];
            var ii=0;
            var cssRule=false;
            do {
                if (styleSheet.cssRules) {
                    cssRule = styleSheet.cssRules[ii];
                } else {
                    cssRule = styleSheet.rules[ii];
                }
                if(cssRule) {
                    if(cssRule.selectorText.toLowerCase()==ruleName) {
                        if(deleteFlag===true) {
                            if(styleSheet.cssRules) {
                                styleSheet.deleteRule(ii);
                            } else {
                                styleSheet.removeRule(ii);
                            }
                            return true;
                        } else {
                            return cssRule;
                        }
                    }
                }
                ii++;
                if(lastRule === cssRule) { lastRuleCnt++; } else { lastRuleCnt = 0; }
                if(lastRuleCnt > 10) { return false; }
                lastRule = cssRule;
            } while (cssRule !== false);
        }
    }
    return false;
}

function killCSSRule(ruleName) {
    return getCSSRule(ruleName, true);
}

function addCSSRule(ruleName) {
    if(document.styleSheets) {
        if(!getCSSRule(ruleName)) {
            if(document.styleSheets[0].addRule) {
                document.styleSheets[0].addRule(ruleName, null,0);
            } else {
                document.styleSheets[0].insertRule(ruleName+' { }', 0);
            }
        }
    }
    return getCSSRule(ruleName);
}

function isElemVisible(obj) {
    if(obj == document) { return true; }
    
    if(!obj) { return false; }
    if(!obj.parentNode) { return false; }
    if(obj.style) {
        if(obj.style.display == 'none') { return false; }
        if(obj.style.visibility == 'hidden') { return false; }
    }

    if(window.getComputedStyle) {
        var style = window.getComputedStyle(obj, "");
        if(style.display == 'none') { return false; }
        if(style.visibility == 'hidden') { return false; }
    }
    
    style = obj.currentStyle;
    if(style) {
        if(style.display == 'none') { return false; }
        if(style.visibility == 'hidden') { return false; }
    }
    
    return isElemVisible(obj.parentNode);
}*/


/**
 * Simplified interface to Timers, utilizes window.setInterval
 */
class Timer
{
    /**
     * Instantiates a new Timer object
     * @param {number} interval Interval of the timer in ms
     * @param {function} tick Callback when the timer ticks
     * @param {boolean} enabled If true, the timer activates right after instantiating the object
     */
    constructor(interval, tick, enabled)
    {
        this.interval = interval || 100;
        this.tick = tick || null
        this.repeat = true;
        this._id = null;
        if(enabled === true)
        {
            this.start();
        }
    }

    /**
     * Start the timer
     */
    start()
    {
        if(this._id != null)
        {
            this.stop();
        }
        var othis = this;
        this._id = window.setInterval(function() { othis._tick(); }, this.interval);
    }

    /**
     * Stop the timer
     */
    stop()
    {
        if(this._id !== null)
        {
            window.clearInterval(this._id);
            this._id = null;
        }
    }
    _tick()
    {
        if(this.repeat == false)
        {
            this.stop();
        }
        if(this.tick instanceof Function)
        {
            this.tick(this);
        }
    }
    /**
     * Returns the status of the timer
     * @returns {boolean} true if running, false if not
     */
    isEnabled()
    {
        return this._id !== null;
    }

    /**
     * Sets a new interval of the timer. The already elapsed time is ignored
     * @param {number} newInterval Interval of the timer in ms
     */
    setInterval(newInterval)
    {
        // caution: this will reset the timer
        this.interval = newInterval;
        if(this._id !== null)
        {
            this.stop();
            this.start();
        }
    }
}

/**
 * Delay events from user input, e.g. to create a response user feedback (load as you type) while keeping the client- & server load reasonable
 */
class DelayedEvent
{
    /**
     * Instantiates a new DelayedEvent object
     * @param {HtmlElement} elem HtmlElement where the event shall be attached to
     * @param {string} event Name of the observed event (e.g. "click")
     * @param {number} delay Delay of the event in ms
     * @param {function} callback Callback function that's called after the delay. 
     *     Callback arguments: associated DelayedEvent-object, HtmlElement, array of events
     */
    constructor(elem, event, delay, callback)
    {
        var self = this;
        this.elem = elem;
        this.delayedEvents = [];
        d.ea(elem, event, function(evt) { self._targetevent(this, evt); });
        this.tmrEvt = new Timer(delay, function() { self._tmrEvent(); }, false);
        this.callback = callback || function() { };
    }

    _targetevent(target, evt)
    {
        this.delayedEvents.push(evt);
        this.tmrEvt.start();
    }

    _tmrEvent()
    {
        this.tmrEvt.stop();
        this.callback(this, this.elem, this.delayedEvents);
        this.delayedEvents.length = 0;
    }

    cancel()
    {
        this.tmrEvt.stop();
        this.delayedEvents.length = 0;
    }
}

class DelayedTrigger
{
    constructor(delay, callback)
    {
        var self = this;
        this.delayedEvents = [];
        this.tmrEvt = new Timer(delay, function() { self._tmrEvent(); }, false);
        this.callback = callback || function() { };
        this.enabled = true;
    }

    trigger()
    {
        if(this.enabled == false)
        {
            return;
        }
        this.delayedEvents.push(arguments);
        this.tmrEvt.start();
    }

    _tmrEvent()
    {
        this.tmrEvt.stop();
        if(this.enabled == false)
        {
            return;
        }
        this.callback(this, this.delayedEvents);
        this.delayedEvents.length = 0;
    }
}

function xhrLoad(filename, successcallback)
{
    var req = new XMLHttpRequest();
    req.addEventListener("load", function() {
        if (req.status >= 200 && req.status < 300) 
        {
            successcallback(this.responseText);
        }
    });
    req.open("GET", filename);
    req.send();
}

/**
 * A simpe stop watch
 */
class Stopwatch
{
    /**
     * Instantiates a new Stopwatch object
     * @param {bool} immediatestart immediately start the stop watch after object instantiation
     */
    constructor(immediatestart)
    {
        this.starttime = null;
        this.stoptime = null;
        if(immediatestart == true)
        {
            this.starttime = new Date().getTime();
        }
    }

    /**
     * Start the stop watch
     */
    start()
    {
        this.starttime = new Date().getTime();
        this.stoptime = null;
    }

    /**
     * Stop the stop watch
     * @returns {number|null} Elapsed time of the stop watch in ms or null if it's not been started
     */
    stop()
    {
        this.stoptime = new Date().getTime();
        if(this.starttime == null) return null;
        return this.stoptime - this.starttime;
    }

    /**
     * Returns the elapsed time of the stop watch
     * @returns {number|null} Elapsed time of the stop watch in ms or null if it's not been started
     */
    getElapsedTime()
    {
        let tmp = this.stoptime;
        if(this.starttime == null) return null;
        if(this.stoptime == null) tmp = new Date().getTime();
        return tmp - this.starttime;
    }
}

function gradient_getcolor(colors, x) {
    /*var iron = [
        [0, 0, 0],
        [60, 0, 86],
        [87, 0, 171],
        [108, 1, 231],
        [125, 4, 255],
        [141, 7, 240],
        [155, 13, 189],
        [167, 20, 109],
        [179, 30, 13],
        [190, 44, 0],
        [200, 60, 0],
        [210, 80, 0],
        [220, 104, 0],
        [229, 133, 0],
        [237, 166, 0],
        [246, 205, 0],
        [254, 249, 0],
    ];*/
    let upperidx = Math.ceil((colors.length - 1) * x);
    if (upperidx == 0) {
        upperidx = 1;
    }
    let uppercol = colors[upperidx];
    let lowercol = colors[upperidx - 1];
    let part = x * (colors.length - 1) - (upperidx - 1);
    return [
        lowercol[0] + (uppercol[0] - lowercol[0]) * part,
        lowercol[1] + (uppercol[1] - lowercol[1]) * part,
        lowercol[2] + (uppercol[2] - lowercol[2]) * part,
    ];
}
function rgba(r, g, b, a) {
    return (
        "rgba(" +
        Math.round(r) +
        "," +
        Math.round(g) +
        "," +
        Math.round(b) +
        "," +
        a +
        ")"
    );
}

function array_group(array, predicate, itemaction)
{
    let result = [];
    array.forEach(o =>
    {
        let groupkey = predicate(o);
        let group = result.find(r => r.key == groupkey);
        if(group == undefined)
        {
            group = {"key" : groupkey, "items" : []};
            result.push(group);
        }
        group.items.push(o);
        if(itemaction != undefined)
        {
            itemaction(group, o, groupkey, array);
        }
    });
    return result;
}

function array_unique(array)
{
    return array.filter((v, i, s) => s.indexOf(v) === i);
}

function array_has_duplicates(array)
{
    return array.some((v, i, s) => s.indexOf(v) !== i);
}