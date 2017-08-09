import { Injectable, NgZone } from '@angular/core';
import { Observable } from "rxjs/Observable";

import { RMPConfig } from './rmp.config';

type CallbackFunc = (error: Error, result: any) => void;

@Injectable()
export class RMPService {

  constructor(private config: RMPConfig,
              private zone: NgZone) { }

  private zoneEncap(cb: CallbackFunc): CallbackFunc {
    return (err, res) => this.zone.run(() => cb(err, res));
  }

  getAccounts(): Observable<string[]> {
    const nodeCbObs = <() => Observable<string[]>>Observable.bindNodeCallback(
      (cb) => this.config.rmp.getAccounts(this.zoneEncap(cb)));
    return nodeCbObs()
      .switchMap((res) => res && res[0] ? Observable.of(res) : Observable.throw(res))
      .retryWhen((err) => err.delay(200));
  }


  signHash(msg, account): Observable<string> {
    const nodeCbObs = Observable.bindNodeCallback(
      (m: string, a: string, cb: CallbackFunc) =>
        this.config.rmp.signHash(m, a, this.zoneEncap(cb)));
    return nodeCbObs(msg, account);
  }

}
