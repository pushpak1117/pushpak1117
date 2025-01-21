package com.rbc.dmi.consumedyantrace.web.rest;

import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.ssl.SSLContextBuilder;
import org.apache.hc.core5.ssl.TrustStrategy;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.http.HttpHost;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.SSLContext;

public class RestProxyTemplate {
    private static final Logger log = LoggerFactory.getLogger(RestProxyTemplate.class);

    private static final Integer connectionTimeOut = 5000; // Timeout in milliseconds
    private static final Integer readTimeOut = 20000; // Timeout in milliseconds
    private static final String PROFILE = System.getenv("SPRING_PROFILES_ACTIVE");
    private static final String LOCAL_ENV = "local";
    private static final String PROXY_HOST = System.getenv("PROXY_HOST");
    private static final String PROXY_PORT = System.getenv("PROXY_PORT");

    private RestTemplate restTemplate;

    public void init() {
        try {
            // Set system properties for TLS
            System.setProperty("https.protocols", "TLSv1.2,TLSv1.3");

            // Configure SSLContext to trust all certificates
            TrustStrategy acceptingTrustStrategy = (chain, authType) -> true;
            SSLContext sslContext = SSLContextBuilder.create()
                    .loadTrustMaterial(null, acceptingTrustStrategy)
                    .build();

            // Create an HTTP client with a connection manager
            PoolingHttpClientConnectionManager connectionManager = new PoolingHttpClientConnectionManager();
            CloseableHttpClient client = HttpClients.custom()
                    .setSSLContext(sslContext)
                    .setConnectionManager(connectionManager)
                    .build();

            // Configure proxy settings if not in a local environment
            if (!LOCAL_ENV.equalsIgnoreCase(PROFILE)) {
                log.info("RestProxyTemplate init: Setting proxy with profile -> {}", PROFILE);
                HttpHost proxy = new HttpHost(PROXY_HOST, Integer.parseInt(PROXY_PORT));
                client = HttpClients.custom()
                        .setSSLContext(sslContext)
                        .setConnectionManager(connectionManager)
                        .setProxy(proxy)
                        .build();
            } else {
                log.info("RestProxyTemplate init: Not setting proxy with profile -> {}", PROFILE);
            }

            // Configure the RestTemplate
            HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory(client);
            factory.setConnectTimeout(connectionTimeOut);
            factory.setReadTimeout(readTimeOut);

            this.restTemplate = new RestTemplate(factory);

        } catch (Exception e) {
            log.error("Error in setting up RestTemplate: {}", e.getMessage(), e);
        }
    }

    public RestTemplate getRestTemplate() {
        this.init();
        return this.restTemplate;
    }
}