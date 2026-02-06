"""
Frida Scripts Integration
Bundled scripts for common security testing tasks
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


@dataclass
class FridaScript:
    """Represents a Frida script"""
    name: str
    description: str
    content: str
    category: str = "general"
    android_only: bool = True
    
    def save(self, path: str) -> bool:
        """Save script to file."""
        try:
            with open(path, 'w') as f:
                f.write(self.content)
            return True
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            return False


# Built-in scripts
BUILTIN_SCRIPTS: Dict[str, FridaScript] = {
    "ssl-pinning-bypass": FridaScript(
        name="ssl-pinning-bypass",
        description="Bypass SSL certificate pinning (supports OkHttp, TrustManager, etc.)",
        category="network",
        content='''/**
 * SSL Pinning Bypass Script
 * Bypasses common SSL pinning implementations
 */

Java.perform(function() {
    console.log("[*] SSL Pinning Bypass loaded");
    
    // TrustManager bypass
    try {
        var TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        
        var TrustManagerImpl = Java.registerClass({
            name: 'com.frida.TrustManager',
            implements: [TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        
        var TrustManagers = [TrustManagerImpl.$new()];
        var sslContext = SSLContext.getInstance("TLS");
        sslContext.init(null, TrustManagers, null);
        SSLContext.setDefault(sslContext);
        console.log("[+] TrustManager bypassed");
    } catch(e) {
        console.log("[-] TrustManager bypass failed: " + e);
    }
    
    // OkHttp3 CertificatePinner bypass
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {
            console.log("[+] OkHttp3 CertificatePinner.check bypassed for: " + hostname);
        };
        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(hostname, peerCertificates) {
            console.log("[+] OkHttp3 CertificatePinner.check bypassed for: " + hostname);
        };
        console.log("[+] OkHttp3 CertificatePinner bypassed");
    } catch(e) {
        console.log("[-] OkHttp3 bypass failed: " + e);
    }
    
    // Trustkit bypass
    try {
        var TrustKit = Java.use('com.datatheorem.android.trustkit.pinning.OkHostnameVerifier');
        TrustKit.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function(hostname, session) {
            console.log("[+] TrustKit bypassed for: " + hostname);
            return true;
        };
        console.log("[+] TrustKit bypassed");
    } catch(e) {
        console.log("[-] TrustKit bypass not applicable");
    }
    
    console.log("[*] SSL Pinning Bypass complete");
});
'''
    ),
    
    "root-detection-bypass": FridaScript(
        name="root-detection-bypass",
        description="Bypass common root detection mechanisms",
        category="security",
        content='''/**
 * Root Detection Bypass Script
 * Bypasses common root detection implementations
 */

Java.perform(function() {
    console.log("[*] Root Detection Bypass loaded");
    
    // Common paths to hide
    var rootPaths = [
        "/system/app/Superuser.apk",
        "/system/xbin/su",
        "/system/bin/su",
        "/sbin/su",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/data/local/su",
        "/su/bin/su",
        "/magisk/.core"
    ];
    
    // File.exists() bypass
    try {
        var File = Java.use('java.io.File');
        File.exists.implementation = function() {
            var path = this.getAbsolutePath();
            for (var i = 0; i < rootPaths.length; i++) {
                if (path.indexOf(rootPaths[i]) !== -1) {
                    console.log("[+] Hiding root path: " + path);
                    return false;
                }
            }
            return this.exists.call(this);
        };
        console.log("[+] File.exists() hooked");
    } catch(e) {
        console.log("[-] File.exists() hook failed: " + e);
    }
    
    // Runtime.exec() bypass for "su" command
    try {
        var Runtime = Java.use('java.lang.Runtime');
        Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
            if (cmd.indexOf("su") !== -1 || cmd.indexOf("which") !== -1) {
                console.log("[+] Blocking command: " + cmd);
                throw new Error("Command not found");
            }
            return this.exec(cmd);
        };
        console.log("[+] Runtime.exec() hooked");
    } catch(e) {
        console.log("[-] Runtime.exec() hook failed: " + e);
    }
    
    // RootBeer bypass
    try {
        var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
        RootBeer.isRooted.implementation = function() {
            console.log("[+] RootBeer.isRooted() bypassed");
            return false;
        };
        RootBeer.isRootedWithoutBusyBoxCheck.implementation = function() {
            console.log("[+] RootBeer.isRootedWithoutBusyBoxCheck() bypassed");
            return false;
        };
        console.log("[+] RootBeer bypassed");
    } catch(e) {
        console.log("[-] RootBeer not found");
    }
    
    // Build.TAGS bypass
    try {
        var Build = Java.use('android.os.Build');
        var tags = Build.TAGS.value;
        if (tags && tags.indexOf("test-keys") !== -1) {
            Build.TAGS.value = "release-keys";
            console.log("[+] Build.TAGS changed to release-keys");
        }
    } catch(e) {
        console.log("[-] Build.TAGS hook failed: " + e);
    }
    
    console.log("[*] Root Detection Bypass complete");
});
'''
    ),
    
    "anti-debug-bypass": FridaScript(
        name="anti-debug-bypass",
        description="Bypass anti-debugging techniques",
        category="security",
        content='''/**
 * Anti-Debug Bypass Script
 * Bypasses common anti-debugging techniques
 */

Java.perform(function() {
    console.log("[*] Anti-Debug Bypass loaded");
    
    // Debug.isDebuggerConnected() bypass
    try {
        var Debug = Java.use('android.os.Debug');
        Debug.isDebuggerConnected.implementation = function() {
            console.log("[+] Debug.isDebuggerConnected() bypassed");
            return false;
        };
        console.log("[+] Debug.isDebuggerConnected() hooked");
    } catch(e) {
        console.log("[-] Debug hook failed: " + e);
    }
    
    // Tracerpid check bypass (native)
    try {
        var fopen = Module.findExportByName("libc.so", "fopen");
        Interceptor.attach(fopen, {
            onEnter: function(args) {
                var path = args[0].readUtf8String();
                if (path && path.indexOf("/proc/") !== -1 && path.indexOf("/status") !== -1) {
                    this.isStatus = true;
                }
            },
            onLeave: function(retval) {
                if (this.isStatus) {
                    console.log("[+] TracerPid check intercepted");
                }
            }
        });
    } catch(e) {
        console.log("[-] Native hook failed: " + e);
    }
    
    // ptrace bypass
    try {
        var ptrace = Module.findExportByName(null, "ptrace");
        if (ptrace) {
            Interceptor.attach(ptrace, {
                onEnter: function(args) {
                    console.log("[+] ptrace() called, returning 0");
                },
                onLeave: function(retval) {
                    retval.replace(0);
                }
            });
            console.log("[+] ptrace() hooked");
        }
    } catch(e) {
        console.log("[-] ptrace hook failed: " + e);
    }
    
    console.log("[*] Anti-Debug Bypass complete");
});
'''
    ),
    
    "method-tracer": FridaScript(
        name="method-tracer",
        description="Trace method calls with arguments and return values",
        category="analysis",
        content='''/**
 * Method Tracer Script
 * Traces method calls with arguments and return values
 * 
 * Usage: Set the CLASS_NAME and METHOD_NAME variables
 */

var CLASS_NAME = ""; // e.g., "com.example.MyClass"
var METHOD_NAME = ""; // e.g., "myMethod" or "*" for all methods

Java.perform(function() {
    console.log("[*] Method Tracer loaded");
    
    if (!CLASS_NAME) {
        console.log("[!] Please set CLASS_NAME variable");
        return;
    }
    
    try {
        var targetClass = Java.use(CLASS_NAME);
        var methods = targetClass.class.getDeclaredMethods();
        
        methods.forEach(function(method) {
            var methodName = method.getName();
            
            if (METHOD_NAME && METHOD_NAME !== "*" && methodName !== METHOD_NAME) {
                return;
            }
            
            var overloads = targetClass[methodName].overloads;
            
            overloads.forEach(function(overload) {
                overload.implementation = function() {
                    var args = Array.prototype.slice.call(arguments);
                    console.log("\\n[+] " + CLASS_NAME + "." + methodName + "()");
                    console.log("    Arguments: " + JSON.stringify(args));
                    
                    var result = this[methodName].apply(this, arguments);
                    
                    console.log("    Return: " + result);
                    return result;
                };
            });
        });
        
        console.log("[+] Hooked " + CLASS_NAME);
    } catch(e) {
        console.log("[-] Error: " + e);
    }
});
'''
    ),
    
    "crypto-logger": FridaScript(
        name="crypto-logger",
        description="Log cryptographic operations (AES, RSA, etc.)",
        category="crypto",
        content='''/**
 * Crypto Logger Script
 * Logs cryptographic operations
 */

function bytesToHex(bytes) {
    var hex = [];
    for (var i = 0; i < bytes.length; i++) {
        hex.push(('0' + (bytes[i] & 0xFF).toString(16)).slice(-2));
    }
    return hex.join('');
}

Java.perform(function() {
    console.log("[*] Crypto Logger loaded");
    
    // Cipher operations
    try {
        var Cipher = Java.use('javax.crypto.Cipher');
        
        Cipher.getInstance.overload('java.lang.String').implementation = function(transformation) {
            console.log("\\n[Cipher] getInstance: " + transformation);
            return this.getInstance(transformation);
        };
        
        Cipher.init.overload('int', 'java.security.Key').implementation = function(opmode, key) {
            var mode = opmode === 1 ? "ENCRYPT" : "DECRYPT";
            console.log("[Cipher] init: " + mode);
            console.log("    Key: " + bytesToHex(key.getEncoded()));
            return this.init(opmode, key);
        };
        
        Cipher.doFinal.overload('[B').implementation = function(input) {
            console.log("[Cipher] doFinal");
            console.log("    Input: " + bytesToHex(input));
            var result = this.doFinal(input);
            console.log("    Output: " + bytesToHex(result));
            return result;
        };
        
        console.log("[+] Cipher hooked");
    } catch(e) {
        console.log("[-] Cipher hook failed: " + e);
    }
    
    // MessageDigest (hashing)
    try {
        var MessageDigest = Java.use('java.security.MessageDigest');
        
        MessageDigest.getInstance.overload('java.lang.String').implementation = function(algorithm) {
            console.log("\\n[Hash] Algorithm: " + algorithm);
            return this.getInstance(algorithm);
        };
        
        MessageDigest.digest.overload('[B').implementation = function(input) {
            console.log("[Hash] Input: " + bytesToHex(input));
            var result = this.digest(input);
            console.log("[Hash] Output: " + bytesToHex(result));
            return result;
        };
        
        console.log("[+] MessageDigest hooked");
    } catch(e) {
        console.log("[-] MessageDigest hook failed: " + e);
    }
    
    // SecretKeySpec
    try {
        var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
        SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, algorithm) {
            console.log("\\n[SecretKeySpec] Algorithm: " + algorithm);
            console.log("    Key: " + bytesToHex(key));
            return this.$init(key, algorithm);
        };
        console.log("[+] SecretKeySpec hooked");
    } catch(e) {
        console.log("[-] SecretKeySpec hook failed: " + e);
    }
    
    console.log("[*] Crypto Logger active");
});
'''
    ),
    
    "http-logger": FridaScript(
        name="http-logger",
        description="Log HTTP/HTTPS requests and responses",
        category="network",
        content='''/**
 * HTTP Logger Script
 * Logs HTTP requests and responses
 */

Java.perform(function() {
    console.log("[*] HTTP Logger loaded");
    
    // OkHttp3 Interceptor
    try {
        var OkHttpClient = Java.use('okhttp3.OkHttpClient');
        var Builder = Java.use('okhttp3.OkHttpClient$Builder');
        var Interceptor = Java.use('okhttp3.Interceptor');
        
        var MyInterceptor = Java.registerClass({
            name: 'com.frida.HttpLogger',
            implements: [Interceptor],
            methods: {
                intercept: function(chain) {
                    var request = chain.request();
                    console.log("\\n[HTTP] " + request.method() + " " + request.url());
                    
                    var headers = request.headers();
                    for (var i = 0; i < headers.size(); i++) {
                        console.log("    " + headers.name(i) + ": " + headers.value(i));
                    }
                    
                    var response = chain.proceed(request);
                    console.log("[HTTP] Response: " + response.code());
                    
                    return response;
                }
            }
        });
        
        console.log("[+] OkHttp3 logger ready");
    } catch(e) {
        console.log("[-] OkHttp3 hook failed: " + e);
    }
    
    // HttpURLConnection
    try {
        var HttpURLConnection = Java.use('java.net.HttpURLConnection');
        
        HttpURLConnection.getInputStream.implementation = function() {
            console.log("\\n[HTTP] " + this.getRequestMethod() + " " + this.getURL());
            console.log("[HTTP] Response: " + this.getResponseCode());
            return this.getInputStream();
        };
        
        console.log("[+] HttpURLConnection hooked");
    } catch(e) {
        console.log("[-] HttpURLConnection hook failed: " + e);
    }
    
    console.log("[*] HTTP Logger active");
});
'''
    ),
}


class ScriptManager:
    """Manages Frida scripts - both built-in and custom"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        config = get_config()
        self.scripts_dir = Path(scripts_dir or config.scripts_dir or Path.home() / ".f4f" / "scripts")
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
    
    def list_builtin(self) -> List[FridaScript]:
        """Get list of built-in scripts."""
        return list(BUILTIN_SCRIPTS.values())
    
    def list_custom(self) -> List[Path]:
        """Get list of custom script files."""
        scripts = []
        for ext in ['*.js', '*.frida']:
            scripts.extend(self.scripts_dir.glob(ext))
        return scripts
    
    def get_builtin(self, name: str) -> Optional[FridaScript]:
        """Get a built-in script by name."""
        return BUILTIN_SCRIPTS.get(name)
    
    def get_custom(self, name: str) -> Optional[str]:
        """Get custom script content by name."""
        script_path = self.scripts_dir / f"{name}.js"
        if not script_path.exists():
            script_path = self.scripts_dir / name
        
        if script_path.exists():
            return script_path.read_text()
        return None
    
    def save_script(self, name: str, content: str) -> Path:
        """Save a custom script."""
        script_path = self.scripts_dir / f"{name}.js"
        script_path.write_text(content)
        logger.info(f"Script saved: {script_path}")
        return script_path
    
    def export_builtin(self, name: str, output_path: Optional[str] = None) -> Optional[Path]:
        """Export a built-in script to file."""
        script = self.get_builtin(name)
        if not script:
            return None
        
        if output_path:
            path = Path(output_path)
        else:
            path = self.scripts_dir / f"{name}.js"
        
        path.write_text(script.content)
        return path
    
    def get_by_category(self, category: str) -> List[FridaScript]:
        """Get built-in scripts by category."""
        return [s for s in BUILTIN_SCRIPTS.values() if s.category == category]
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list(set(s.category for s in BUILTIN_SCRIPTS.values()))
