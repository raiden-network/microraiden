import { Injectable } from '@angular/core';
import { Observable } from "rxjs/Observable";

import { RMPConfig } from './rmp.config';

@Injectable()
export class RMPService {

  constructor(private config: RMPConfig) { }

  getAccounts() {
    return this.config.rmp.getAccounts();
  }

  signMessage(msg, account): Observable<string> {
    const nb = <(m: string, a: string) => Observable<string>>Observable.bindNodeCallback(this.config.rmp.signMessage);
    return nb(msg, account);
  }

}
