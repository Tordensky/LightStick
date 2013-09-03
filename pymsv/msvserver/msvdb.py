# Written by Ingar Arntzen, Norut

import sqlite3
import time
import util.msvutil as msvutil
from util.msvutil import P,V,A,T, compute_msv
from util.mylog import *


##############################################
# SET MSV DATABASE
##############################################

CREATE_MSV_TABLE = '''CREATE TABLE if not exists msvs (
msvid INTEGER PRIMARY KEY AUTOINCREMENT,
pos REAL,
vel REAL,
acc REAL,
ts  REAL,
eventid INTEGER,
r_start REAL,
r_end REAL
)'''

SQL_GET_MSV = "SELECT * from msvs WHERE msvid=?"
SQL_UPDATE_MSV = "UPDATE msvs SET pos=?, vel=?, acc=?, ts=?, eventid=? WHERE msvid=?"
SQL_CREATE_MSV = "INSERT into msvs values (NULL, ?, ?, ?, ?, 0, ?, ?)"
SQL_MOVING_MSVS = "SELECT * from msvs WHERE ((r_start IS NOT NULL OR r_end IS NOT NULL) AND (vel != 0.0 OR acc != 0.0))"
SQL_DELETE_MSV = "DELETE from msvs WHERE msvid=?"

def get_msv_state_from_row(row):
    """Create msv state from row"""
    return {
        'msvid': row['msvid'],
        'vector': (row['pos'], row['vel'], row['acc'], row['ts']),
        'eventid': row['eventid'],
        'range': [row['r_start'], row['r_end']],
        }


class MsvDatabase:

    """This implements the database API over a sqlite3 database for
    MSV's 

    msv_data - a dictionary specifying the footprint of a MSV
    {
    'msvid': msvid,
    'range': [r_start,r_end],
    'vector': (p, v, a, ts),
    'eventid': eventid,
    }

    msv_data may be used as parameter to create new MSVs. If so,
    'eventid' and 'msvid' will be ignored (and are not required).
    If 'vector' is specified this will become the internal state of the new msv as well.
    This provides a handy way of forking/duplicating MSV's. If 'vector' is not specified,
    default values are (r_start, 0.0, 0.0, time.time()). For MSV's with no 'range' specified,
    default value is (0.0, 0.0, 0.0, time.time())
    """

    def __init__(self, filename=None):
        self._filename = filename if filename != None else ":memory:"
        self._conn = None
        # Make sure Database Exists
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute(CREATE_MSV_TABLE)
            c.close()
            conn.commit()
        except sqlite3.Error as e:
            MyLog().log.exception("SQL error, ignoring");
            print e
            pass
        #self.conn.close()

    def get_connection(self):
        """Return sqlite3 connection object"""
        if not self._conn:
            self._conn = sqlite3.connect(self._filename)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        self._conn.commit()
        self._conn.close()

    def create_msvs(self, cursor, msv_data_list=[]):
        """Create MSVs without SET membership.
        Returns list of created msvids. Returns msvids of created MSV's.
        """
        if not msv_data_list:
            return

        # Create
        for msv_data in msv_data_list:
            try:
                range = msv_data.get('range', [None, None])
            except:
                range = [None, None]
            r_start, r_end = range[0], range[1]
            p = r_start if r_start != None else 0.0
            v = 0.0
            a = 0.0
            ts = time.time()
            t = (p,v,a,ts,r_start,r_end)
            cursor.execute(SQL_CREATE_MSV, t)
            msvid = cursor.lastrowid
            msv_data['msvid'] = msvid
        
        # Update and construct result
        result_list = []
        for msv_data in msv_data_list:
            try:
                if msv_data.has_key('vector') and msv_data['vector'] != None:
                    res = self.update_msvs(cursor, [msv_data])[0]
                else:
                    res = self.get_msv_data_list(cursor, [msv_data['msvid']])[0]
                if res != None:
                    result_list.append(res)
            except:
                MyLog().log.exception("Exception updating msvs");
                continue
        return result_list

    def get_msv_data_list(self, cursor, msvid_list):
        """Get list of msv_data given list of msvids."""
        result = []
        for msvid in msvid_list:
            cursor.execute(SQL_GET_MSV, (msvid,))
            row = cursor.fetchone()
            if row == None:
                continue      
            result.append(get_msv_state_from_row(row))
        return result

    def get_moving_msvs_with_range_restrictions (self, cursor):
        """Get the msvid of all msvs that have range restrictions and are moving."""
        result = []
        cursor.execute(SQL_MOVING_MSVS)
        while True:
            row = cursor.fetchone()
            if row == None: 
                break
            result.append(get_msv_state_from_row(row))
        return result

    def update_msvs(self, cursor, msv_data_list):
        """Update msvs.  

        - relative implies that the parameter new_vector is not
        absolute, but should rather be added to the existing vector.
        
        - valid specifies an eventid. The update is only valid if this
          eventid matches the current eventid of the msv (before this
          update).  If not, the update is deemed invalid and dropped,
          This is used to ensure that delayed updates (e.g. timeouts
          associated range violations are dropped if any update was
          processed in between)

          
          TODO : make sure same msvid isnt updated multiple times

        """
        res = []
        ts_now = time.time()
        for msv_data in msv_data_list:
            msvid = msv_data['msvid']
            new_vector = msv_data['vector']
            relative = msv_data.get('relative', False)
            valid = msv_data.get('valid', None)
        
            # BEGIN Transaction

            cursor.execute(SQL_GET_MSV, (msvid,))
            row = cursor.fetchone()
            if row == None: 
                return

            # Check that timeout-updates are valid.
            if valid != None and valid != row['eventid']:
                return

            # Initialise Variables
            old_vector = (row['pos'], row['vel'], row['acc'], row['ts'])
            now_vector = compute_msv(old_vector, ts_now)

            p,v,a = new_vector[:3]

            if relative:
                # Create absolute update vector
                p = now_vector[P] + p if p != None else now_vector[P] 
                v = now_vector[V] + v if v != None else now_vector[V] 
                a = now_vector[A] + a if a != None else now_vector[A] 
            else:
                # Fill in missing vectors
                if p == None: p = now_vector[P]
                if v == None: v = now_vector[V]
                if a == None: a = now_vector[A]

            # Check Range Restrictions
            r_start, r_end = row['r_start'], row['r_end']
            if r_end != None and p >= r_end:
                p = r_end
                if v > 0.0: v = 0.0
                if (v == 0.0 and a > 0.0): a = 0.0
            elif r_start != None and p <= r_start:
                p = r_start
                if v < 0.0: v = 0.0
                if (v == 0.0 and a < 0.0): a = 0.0

            # Update Database
            eventid = row['eventid'] + 1
            cursor.execute(SQL_UPDATE_MSV, (p,v,a, ts_now, eventid, msvid))
            ok = True if cursor.rowcount == 1 else False

            # END Transaction

            if ok:
                res.append( {
                    'msvid': msvid,
                    'eventid': eventid,
                    'old_vector': old_vector,
                    'now_vector': now_vector,
                    'vector': (p,v,a,ts_now),
                    'range': [row['r_start'], row['r_end']],
                })
        return res

    def delete_msvs(self, cursor, msvid_list):
        """Delete MSV"""
        deleted_msvid_list = []
        for msvid in msvid_list:
            cursor.execute(SQL_DELETE_MSV, (msvid,))
            if cursor.rowcount == 1:
                deleted_msvid_list.append(msvid)
        return deleted_msvid_list






