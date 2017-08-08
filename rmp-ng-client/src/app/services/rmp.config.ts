import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

//declare var RaidenMicropaymentsClient;
import { RaidenMicropaymentsClient } from '../../lib/rmp.js';

@Injectable()
export class RMPConfig {
    public config: { web3url: string };
    public rmp: any;

    constructor(private http: HttpClient) { }

    load(url: string) {
        return new Promise((resolve) => {
            this.http.get<{ web3url: string }>(url)
                .subscribe((config) => {
                    this.config = config;
                    this.rmp = new RaidenMicropaymentsClient(config.web3url);
                    resolve();
                });
        });
    }
}

